var data;

// grid configs
const grid = canvasDatagrid({
  parentNode: document.getElementById("gridContainer"),
  data,
  showRowNumbers: true,
  multipleSelection: true,
  allowMovingSelection: true,
  multiLine: true,
  pasteText: false,
  editable: false,
});

let keyed;
// Print JSON only when selection stops (mouseup)
grid.addEventListener("mouseup", () => {
  var selectedCells = grid.selectedCells;

  // get first nth empty cell
  let empty_cell = 0;
  for (const cell of selectedCells) {
    if (cell == null) empty_cell++;
  }

  // get current cell
  current_cell = empty_cell + 1;

  // get list of json selected items
  selectedCells = selectedCells.filter((cell) => cell !== null);

  // map to keys
  keyed = Object.fromEntries(
    selectedCells.map((item, i) => [current_cell + i, item]),
  );
  console.log(keyed);
});

document.addEventListener("copy", (e) => {
  if (keyed) {
    e.preventDefault();
    console.log("Copy detected!");

    // (optional) change clipboard content
    e.clipboardData.setData("text/plain", JSON.stringify(keyed));
  }
});

document.addEventListener("paste", (e) => {
  console.log(grid.selectedCells);
});

// Button to export JSON
document.getElementById("exportRaw").onclick = () => {
  const json = JSON.stringify(grid.selectedCells, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "selectedCells.json";
  a.click();
};

document.getElementById("copyBtn").onclick = () => {
  if (keyed) {
    const codeBlock = document.getElementById("highlightedCode");
    codeBlock.textContent = JSON.stringify(keyed, null, 2);

    // highlight
    hljs.highlightElement(codeBlock);
  }
};

// swap data test
document.getElementById("hi").onclick = () => {
  console.log(grid.data);
};

// swap data test
function pollServer() {
  $.ajax({
    url: "data.php",
    method: "GET",
    success: function (data) {
      console.log("Server response:", data);
    },
    error: function (err) {
      console.error("Error:", err);
    },
  });
}

// Run every 5 seconds
setInterval(pollServer, 5000);

const items = ["Apple", "Banana", "Orange", "Mango", "Grapes"];

$("#search").on("input", function () {
  const val = $(this).val().toLowerCase();
  const matches = items.filter((item) => item.toLowerCase().includes(val));
  const html = matches
    .map((m) => `<div class="suggestion">${m}</div>`)
    .join("");
  $("#suggestions").html(html);
});

$("#suggestions").on("click", ".suggestion", function () {
  $("#search").val($(this).text());
  $("#suggestions").empty();
});

const dataset = [
  { x: 0, y: 10 },
  { x: 1, y: 15 },
  { x: 2, y: 8 },
  { x: 3, y: 20 },
  { x: 4, y: 18 },
  { x: 5, y: 25 },
];

const margin = { top: 40, right: 30, bottom: 50, left: 50 };
const width = 600 - margin.left - margin.right;
const height = 400 - margin.top - margin.bottom;

const svg = d3
  .select("#chart")
  .append("svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom)
  .append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// X & Y scales
const x = d3
  .scaleLinear()
  .domain(d3.extent(dataset, (d) => d.x))
  .range([0, width]);

const y = d3
  .scaleLinear()
  .domain([0, d3.max(dataset, (d) => d.y)])
  .range([height, 0]);

// X & Y axes
svg
  .append("g")
  .attr("transform", `translate(0,${height})`)
  .call(d3.axisBottom(x));

svg.append("g").call(d3.axisLeft(y));

// Grid lines
svg
  .append("g")
  .call(d3.axisLeft(y).tickSize(-width).tickFormat(""))
  .selectAll(".tick line")
  .attr("class", "grid");

// Line generator (smooth curve)
const line = d3
  .line()
  .x((d) => x(d.x))
  .y((d) => y(d.y))
  .curve(d3.curveMonotoneX);

// Draw line
svg.append("path").datum(dataset).attr("class", "line").attr("d", line);

// Tooltip
const tooltip = d3.select(".tooltip");

// Draw dots and tooltip
svg
  .selectAll(".dot")
  .data(dataset)
  .join("circle")
  .attr("class", "dot")
  .attr("cx", (d) => x(d.x))
  .attr("cy", (d) => y(d.y))
  .attr("r", 5)
  .on("mouseover", (event, d) => {
    tooltip
      .style("opacity", 1)
      .html(`x: ${d.x}<br>y: ${d.y}`)
      .style("left", event.pageX + 10 + "px")
      .style("top", event.pageY - 25 + "px");
  })
  .on("mousemove", (event) => {
    tooltip
      .style("left", event.pageX + 10 + "px")
      .style("top", event.pageY - 25 + "px");
  })
  .on("mouseout", () => tooltip.style("opacity", 0));

// Axis labels
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", height + 40)
  .attr("text-anchor", "middle")
  .text("X Axis");

svg
  .append("text")
  .attr("x", -height / 2)
  .attr("y", -35)
  .attr("transform", "rotate(-90)")
  .attr("text-anchor", "middle")
  .text("Y Axis");

// Chart title
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", -10)
  .attr("text-anchor", "middle")
  .attr("font-size", "16px")
  .attr("font-weight", "bold")
  .text("Curved Line Chart");

grid.addEventListener("contextmenu", (e) => {
  e.items.length = 0;
  e.items.push({
    title: `<input type="text" placeholder="Type here"
             onkeydown="if(event.key==='Enter'){alert('You typed: '+this.value);}"
             onclick="event.stopPropagation()">`,
    action: () => {},
  });
});
