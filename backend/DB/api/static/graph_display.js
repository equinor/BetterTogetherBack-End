let simulation;
let links = {};
let node = {};

let width = document.getElementById("content").clientWidth;
let height = document.getElementById("content").clientHeight;

let radius = width / 30;

let token = (new URL(document.location)).searchParams.get("token");

let days =
    function () {
    if (parseInt((new URL(document.location)).searchParams.get("days"))) {
        return  parseInt((new URL(document.location)).searchParams.get("days"));
    }
    return 30;
};

let setHeight = d3.select("#content")
    .attr("height", window.innerHeight);

d3.json("api/user/active?token=" + token, (users) => {
    let status = {};
    let edgeUsers = {};
    function updateData(){
        //Unix time stamp x days ago
        let date = Date.now()-1000*3600*24*days();
        d3.json("api/pair/count_pair/"+date.toString()+"?token=" + token, (edges) => {
            d3.json("api/reward/progress?token=" + token, (newStatus) => {
                status = newStatus;
                edgeUsers = edges;
                let cakePercent = (status.cake_count / status.cake_thres) * 100;
                let pizzaPercent = (status.pizza_count / status.pizza_thres) * 100;
                d3.selectAll("span").remove();
                d3.select("#cake-percentage")
                    .attr("style", "width:" + cakePercent + "%");

                d3.select("#cake-text")
                    .append("span")
                    .text(status.cake_count + "/" + status.cake_thres);

                d3.select("#pizza-percentage")
                    .attr("style", "width:" + pizzaPercent + "%");

                d3.select("#pizza-text")
                    .append("span")
                    .text(status.pizza_count + "/" + status.pizza_thres);

                let userIndices = {};
                users.forEach((v, i) => userIndices[v.username] = i);
                let newLinks = edgeUsers.map((v) => ({
                    "source": userIndices[v.source],
                    "target": userIndices[v.target],
                    "total": v.total,
                }));
                simulation.force("link", d3.forceLink().links(newLinks).strength(1));
                if(newLinks.length !== links.length){
                    simulation.alpha(0.5).restart();
                } else {
                    simulation.restart();
                }
                links = newLinks;
            });
        });
    }

    //drag handler
    //d is the node
    function dragStart(d) {
        if (!d3.event.active) {
            simulation.alphaTarget(0.3).restart();
        }
        d.fx = d.x;
        d.fy = d.y;
    }

    function drag(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    function dragEnd(d) {
        if (!d3.event.active) {
            simulation.alphaTarget(0);
        }
        d.fx = null;
        d.fy = null;
    }

    function isLastPairEdge(edge) {
        return ((edge.source.username === status.last_pair[0] &&
            edge.target.username === status.last_pair[1]) ||
            (edge.source.username === status.last_pair[1] && edge.target.username === status.last_pair[0]));
    }

    function updateLinks() {
        let classLink = d3.select("#links")
            .selectAll("line")
            .data(links);
        classLink.enter()
            .append("line")
            .merge(classLink)
            .attr("stroke-width", (d) => 4*Math.log2(d.total)+1)
            .attr("stroke", (d) => {
                if (isLastPairEdge(d)) {
                    return "rgba(255, 18, 67, 1)";
                } else {
                    return "rgba(0, 112, 121, 1)";
                }
            })
            .attr("x1", (d) => d.source.x)
            .attr("y1", (d) => d.source.y)
            .attr("x2", (d) => d.target.x)
            .attr("y2", (d) => d.target.y);

        classLink.exit().remove();
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

    function updateNodes() {
        node.enter()
            .append("circle")
            .attr("r", radius)
            .merge(node)
            .attr("cx", (d) => d.x = Math.max(radius, Math.min(width - radius, d.x)))
            .attr("cy", (d) => d.y = Math.max(radius, Math.min(height - radius, d.y)))
            .on("mouseover", handleMouseOver)
            .on("mouseout", handleMouseOut);
        node.exit().remove();
    }

    function rewardBlink() {
        if (status["cake_count"] >= status["cake_thres"]) {
            d3.select("#cake")
                .attr("class","all-rounded reward-blink");
        } else {
            d3.select("#cake")
                .attr("class", "all-rounded");
        }
        if (status["pizza_count"] >= status["pizza_thres"]) {
            d3.select("#pizza")
                .attr("class","all-rounded reward-blink");
        } else {
           d3.select("#pizza")
                .attr("class", "all-rounded");
        }
    }

    function ticked() {
        width = document.getElementById("content").clientWidth;
        height = document.getElementById("content").clientHeight;
        updateNodes();
        updateLinks();
        rewardBlink();
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
        .attr("patternContentUnits", "objectBoundingBox")
        .append("image")
        .attr("height", 1)
        .attr("width", 1)
        .attr("preserveAspectRatio", "none")
        .attr("href", (d) => {
            if (d.image === "unknown") {
                return "../static/images/default.png/?token=" + token;
            } else {
                return "../static/images/" + d.username + "?token=" + token;
            }
        });

    //Add nodes to <class>-es
    node = d3.select("#circles")
        .selectAll("circle")
        .data(users)
        .enter().append("circle")
        .attr("class", "user_node")
        .attr("r", radius)
        .attr("fill", (d) => ("url(#" + d.username + ")"));

    updateData();
    setInterval(updateData, 5000);

    simulation = d3.forceSimulation(users)
        .force("collision", d3.forceCollide().radius(radius + 20))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("charge", d3.forceManyBody())
        .force("link", d3.forceLink().links(links).strength(1))
        .on("tick", ticked);


    let dragHandler = d3.drag()
        .on("start", dragStart)
        .on("drag", drag)
        .on("end", dragEnd);

    dragHandler(node);
});
