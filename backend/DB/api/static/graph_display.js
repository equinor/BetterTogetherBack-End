let width = 1500, height = 750;

let radius = width / 50;

d3.json("api/user/all?token=TEST", (users) => {

    d3.json("api/pair/count_pair?token=TEST", (edge_users) => {

        d3.json("status/data?token=TEST", (status) => {


            let user_indices = {};
            users.forEach((v, i) => user_indices[v.username] = i);
            let links = edge_users.map((v) => ({
                'source': user_indices[v.source],
                'target': user_indices[v.target],
                'total': v.total,
            }));


            let setCakeProgress = d3.select('#cake')
                .attr('style', "width:" + status.cake_count / status.cake_thres * 100 + "%")
                .attr("aria-valuemax", status.cake_thres)
                .text(status.cake_count.toString() + "/" + status.cake_thres.toString());


            let setPizzaProgress = d3.select('#pizza')
                .attr('style', "width:" + status.pizza_count / status.pizza_thres * 100 + "%")
                .attr("aria-valuemax", status.pizza_thres)
                .text(status.pizza_count.toString() + "/" + status.pizza_thres.toString());

            let setClaimable = d3. select('#status_bar')
                .append("div")
                .text("Claimable cake: "+ status['unused_cake'] +
                    " Claimable pizza: "+ status['unused_pizza']);


            //Add patterns to images
            let defs = d3.select('#patterns_svg')
                .selectAll('pattern')
                .data(users)
                .enter()
                .append('pattern')
                .attr('id', (d) => d.username)
                .attr('height', "100%")
                .attr('width', "100%")
                .attr('patternContentUnits', 'objectBoundingBox')
                .append('image')
                .attr('height', 1)
                .attr('width', 1)
                .attr('preserveAspectRatio', 'none')
                .attr('href', (d) => {
                    if (d.image === "unknown") {
                        return "../static/images/default.png/?token=TEST"
                    } else {
                        return "../static/images/"+ d.username + ".png/?token=TEST"
                    }
                });


            //Add nodes to <class>-es
            let node = d3.select('#circles')
                .selectAll('circle')
                .data(users)
                .enter().append('circle')
                .attr('class', 'user_node')
                .attr('r', radius)
                .attr('fill', (d) => ('url(#' + d.username + ')'));


            let simulation = d3.forceSimulation(users)
                .force('collision', d3.forceCollide().radius(radius + 10))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('charge', d3.forceManyBody().strength(10))
                .force('link', d3.forceLink().links(links).strength(1))
                //.velocityDecay(0.01)
                .on('tick', ticked);


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


            function updateLinks() {
                let class_link = d3.select('#links')
                    .selectAll('line')
                    .data(links);

                class_link.enter()
                    .append('line')
                    .merge(class_link)
                    .attr('stroke-width', (d) => d.total)
                    .attr('stroke', (d) => {
                        if (d.source.username === status.last_pair[0] && d.target.username === status.last_pair[1]) {
                            return 'red'
                        } else {
                            return 'black'
                        }
                    })
                    .attr('x1', (d) => d.source.x)
                    .attr('y1', (d) => d.source.y)
                    .attr('x2', (d) => d.target.x)
                    .attr('y2', (d) => d.target.y);

                class_link.exit().remove()
            }

            function updateNodes() {
                node.enter()
                    .append('circle')
                    .attr('r', radius)
                    .merge(node)
                    .attr('cx', (d) => d.x = Math.max(radius, Math.min(width - radius, d.x)))
                    .attr('cy', (d) => d.y = Math.max(radius, Math.min(height - radius, d.y)))
                    .on('mouseover', handleMouseOver)
                    .on('mouseout', handleMouseOut);
                node.exit().remove();
            }

            function ticked() {
                updateNodes();
                updateLinks();
            }

            function handleMouseOver(d, i) {
                d3.select(this)
                    .attr("r", 1.2 * radius);

                d3.select('svg').append('text')
                    .attr('id', 'object_selected')
                    .attr('x', () => d.x + radius * 1.3)
                    .attr('y', () => d.y - height / 35)
                    .text(() => d.name);
            }

            function handleMouseOut(d, i) {
                d3.select(this)
                    .attr('r', radius);
                d3.select('#object_selected').remove();
            }
        });
    });
});
