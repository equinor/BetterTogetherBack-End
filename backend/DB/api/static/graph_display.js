let width = document.getElementById("content").clientWidth;
let height = document.getElementById("content").clientHeight;

let radius = width / 30;

let token = (new URL(document.location)).searchParams.get("token");

let set_height = d3.select("#content")
    .attr("height", window.innerHeight);


d3.json("api/user/all?token=" + token, (users) => {

    d3.json("api/pair/count_pair?token=" + token, (edge_users) => {

        d3.json("api/reward/progress?token=" + token, (status) => {


            let user_indices = {};
            users.forEach((v, i) => user_indices[v.username] = i);
            let links = edge_users.map((v) => ({
                "source": user_indices[v.source],
                "target": user_indices[v.target],
                "total": v.total,
            }));

            let cake_percent = (status.cake_count / status.cake_thres) * 100;
            let pizza_percent = (status.pizza_count / status.pizza_thres) * 100;

            let set_progress_cake = d3.select('#cake-percentage')
                .attr('style', "width:" + cake_percent + "%")
                .append('span')
                .text(status.cake_count + "/" + status.cake_thres);

            let set_progress_pizza = d3.select('#pizza-percentage')
                .attr('style', "width:" + pizza_percent + "%")
                .append('span')
                .text(status.pizza_count + "/" + status.pizza_thres);

            function rewardBlink() {
                if (status["unused_cake"] > -1) {
                    d3.select("#cake")
                        .attr("class","all-rounded reward-blink")
                }
                if (status["unused_pizza"] > 0) {
                    d3.select("#pizza")
                        .attr("class","all-rounded reward-blink")
                }
            }

            //Add patterns to images
            let defs = d3.select("#patterns_svg")
                .selectAll("pattern")
                .data(users)
                .enter()
                .append("pattern")
                .attr("id", (d) => d.username)
                .attr("height", "100%")
                .attr("width", "100%")
                .attr('patternContentUnits', 'objectBoundingBox')
                .append('image')
                .attr('height', 1)
                .attr('width', 1)
                .attr('preserveAspectRatio', 'none')
                .attr("href", (d) => {
                    if (d.image === "unknown") {
                        return "../static/images/default.png/?token=" + token;
                    } else {
                        return "../static/images/" + d.username + ".png/?token=" + token;
                    }
                });


            //Add nodes to <class>-es
            let node = d3.select("#circles")
                .selectAll("circle")
                .data(users)
                .enter().append("circle")
                .attr("class", "user_node")
                .attr("r", radius)
                .attr("fill", (d) => ("url(#" + d.username + ")"));


            let simulation = d3.forceSimulation(users)
                .force("collision", d3.forceCollide().radius(radius + 10))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("charge", d3.forceManyBody().strength(10))
                .force("link", d3.forceLink().links(links).strength(1))
                //.velocityDecay(0.01)
                .on("tick", ticked);


            let drag_handler = d3.drag()
                .on("start", drag_start)
                .on("drag", drag_drag)
                .on("end", drag_end);

            drag_handler(node);

            //drag handler
            //d is the node
            function drag_start(d) {
                if (!d3.event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }

            function drag_drag(d) {
                d.fx = d3.event.x;
                d.fy = d3.event.y;
            }

            function drag_end(d) {
                if (!d3.event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }

            function isLastPairEdge(edge) {
                return ((edge.source.username === status.last_pair[0] &&
                    edge.target.username === status.last_pair[1]) ||
                    (edge.source.username === status.last_pair[1] && edge.target.username === status.last_pair[0]));
            }

            function updateLinks() {
                let class_link = d3.select("#links")
                    .selectAll("line")
                    .data(links);

                class_link.enter()
                    .append("line")
                    .merge(class_link)
                    .attr("stroke-width", (d) => d.total)
                    .attr("stroke", (d) => {
                        if (isLastPairEdge(d)) {
                            return "red";
                        } else {
                            return "black";
                        }
                    })
                    .attr("x1", (d) => d.source.x)
                    .attr("y1", (d) => d.source.y)
                    .attr("x2", (d) => d.target.x)
                    .attr("y2", (d) => d.target.y);

                class_link.exit().remove()
            }

            function updateNodes() {
                node.enter()
                    .append("circle")
                    .attr("r", radius)
                    .merge(node)
                    .attr("cx", (d) => d.x = Math.max(radius, Math.min(width - radius, d.x - radius)))
                    .attr("cy", (d) => d.y = Math.max(radius, Math.min(height - radius, d.y - radius)))
                    .on("mouseover", handleMouseOver)
                    .on("mouseout", handleMouseOut);
                node.exit().remove();
            }

            function ticked() {
                width = document.getElementById("content").clientWidth;
                height = document.getElementById("content").clientHeight;
                updateNodes();
                updateLinks();
                rewardBlink();
            }

            function handleMouseOver(d, i) {
                d3.select(this)
                    .attr("r", 1.2 * radius);

                d3.select("svg").append("text")
                    .attr("id", "object_selected")
                    .attr("x", () => d.x + radius * 1.3)
                    .attr("y", () => d.y - height / 35)
                    .text(() => d.name);
            }

            function handleMouseOut(d, i) {
                d3.select(this)
                    .attr("r", radius);
                d3.select("#object_selected").remove();
            }
        });
    });
});
