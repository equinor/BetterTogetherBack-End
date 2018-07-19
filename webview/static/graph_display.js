let width = 1500, height = 750;

let cake = 20, pizza = 40;
let cake_thres = 30, pizza_thres = 70;

let radius = width / 50;

d3.json("json_users", (users) => {

    d3.json("json_pairs", (edge_users) => {

    var setCakeProgress = d3.select('#cake')
        .attr('style', "width:"+cake/cake_thres*100+"%")
        .attr("aria-valuemax", cake_thres)
        .text(cake.toString()+"/"+cake_thres.toString());

    var setPizzaProgress = d3.select('#pizza')
        .attr('style', "width:"+pizza/pizza_thres*100+"%")
        .attr("aria-valuemax", pizza_thres)
        .text(pizza.toString()+"/"+pizza_thres.toString());

      //Add patterns to images
     var defs = d3.select('#patterns_svg')
            .selectAll('pattern')
            .data(users)
            .enter()
            .append('pattern')
            .attr('id',function(d){
            return d.username})
            .attr('height', "100%")
            .attr('width', "100%")
            .attr('patternContentUnits','objectBoundingBox')
            .append('image')
            .attr('height',1)
            .attr('width',1)
            .attr('preserveAspectRatio','none')
            .attr('href', function(d){
                if (d.image === "unknown") {
                    return "../static/default.png"
                } else {
                    return d.image}});

    //Add nodes to <class>-es
    var node = d3.select('#circles')
            .selectAll('circle')
            .data(users)
            .enter().append('circle')
            .attr('class','user_node')
            .attr('r', radius)
            .attr('fill', function(d){
            return 'url(#'+d.username+')'});

    var simulation = d3.forceSimulation(users)
        .force('collision', d3.forceCollide().radius(radius + 10))
        .force('center', d3.forceCenter(width/2, height/2))
        .force('charge', d3.forceManyBody().strength(5))
        .force('link', d3.forceLink().links(edge_users).strength(1))
        .on('tick', ticked);


    var drag_handler = d3.drag()
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
        var class_link = d3.select('#links')
            .selectAll('line')
            .data(edge_users);

        class_link.enter()
            .append('line')
            .merge(class_link)
            .attr('stroke-width', (d) => d.total)
            .attr('x1', (d) => d.source.x)
            .attr('y1', (d) => d.source.y)
            .attr('x2', (d) => d.target.x)
            .attr('y2', (d) =>  d.target.y);
        class_link.exit().remove()
    }

    function updateNodes() {
      node.enter()
        .append('circle')
        .attr('r', radius)
        .merge(node)
        .attr('cx', function(d) {
          return d.x = Math.max(radius, Math.min(width - radius, d.x));
        })
        .attr('cy', function(d) {
          return d.y = Math.max(radius, Math.min(height - radius, d.y));
        })
        .on('mouseover', handleMouseOver)
        .on('mouseout', handleMouseOut);
      node.exit().remove()
    }

    function ticked() {
        updateNodes();
        updateLinks();
    }

    function handleMouseOver(d, i){
      d3.select(this)
      .attr("r", 1.2 * radius);

      d3.select('svg').append('text')
      .attr('id', 'object_selected')
      .attr('x', function() { return d.x + radius*1.3; })
      .attr('y', function() { return d.y - height/35; })
      .text(function() { return d.name;});
    }

    function handleMouseOut(d, i){
      d3.select(this)
      .attr('r', radius);
      d3.select('#object_selected').remove();
    }
    });

});
