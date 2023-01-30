const textWithMark = $(".js-with-mark");
const textWithoutMark = $(".js-without-mark");
const URL = "http://127.0.0.1:30701/ui";
jQuery.ajax({
  url: URL + "/get-all-data",
  type: "GET",
  success: function (data) {
    drawChart(Object.values(data));
    // console.log(data)
  },
  error: function (xhr, status, error) {
    alert(xhr.responseText);
  },
});
setInterval(callAPI, 10000);
let barChartCanvas;
let barChartCanvas2;

function callAPI() {
  jQuery.ajax({
    url: URL + "/get-all-data",
    type: "GET",
    success: function (data) {
      drawChart(Object.values(data));
    },
    error: function (xhr, status, error) {
      alert(xhr.responseText);
    },
  });
}
const ctx = document.getElementById("myChart");
function drawChart(dataRecognizations) {
  if (barChartCanvas !== undefined) {
    barChartCanvas.destroy();
  }
  textWithMark.text(dataRecognizations[0]);
  textWithoutMark.text(dataRecognizations[1]);
  const labels = ["Mask", "Without Mask", "", "", ""];
  const data = {
    labels: labels,
    datasets: [
      {
        label: "Recognization Face Mask",
        data: dataRecognizations,
        backgroundColor: [
          "rgba(255, 99, 132, 0.2)",
          "rgba(54, 162, 235, 0.2)",
          "rgba(153, 102, 255, 0.2)",
        ],
        borderColor: [
          "rgb(255, 99, 132)",
          "rgb(54, 162, 235)",
          "rgb(153, 102, 255)",
        ],
        borderWidth: 1,
      },
    ],
  };
  barChartCanvas = new Chart(ctx, {
    type: "bar",
    data: data,
    options: {
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });
}
function getHour(timestamp) {
  const date1 = new Date(timestamp);
  return date1.getHours();
}
function getDate(timestamp) {
  const date = new Date(timestamp);
  return date.getDate();
}
function getMonth(timestamp) {
  const date = new Date(timestamp);
  const month = date.getMonth();
  return month;
}
function getYear(timestamp) {
  const date = new Date(timestamp);
  return date.getFullYear(timestamp);
}

listMask = [];
listWithoutMask = [];
const selectMonth = $(".select-month-js");
const selectYear = $(".select-year-js");
const date = new Date();
changeTimeByDay();
setInterval(callAPI3, 10000);
$(".btn-choose-js").click(callAPI3);
function callAPI3() {
  const typeFilter = $(".select-type-js").val();
  console.log(typeFilter);
  switch (typeFilter) {
    case "YEAR":
      changeTimeByYear(selectYear.val());
      break;
    case "MONTH":
      changeTimeByMonth(selectMonth.val(), selectYear.val());
      break;
    case "DAY":
      changeTimeByDay();
      break;
  }
}
$(".select-type-js").change(function () {
  const typeFilter = $(".select-type-js").val();
  if (typeFilter === "YEAR") {
    selectMonth.attr("disabled", true);
    selectYear.attr("disabled", false);
  } else {
    if (typeFilter === "DAY") {
      selectMonth.attr("disabled", true);
      selectYear.attr("disabled", true);
    } else {
      selectMonth.attr("disabled", false);
      selectYear.attr("disabled", false);
    }
  }
});
function changeTimeByDay() {
  jQuery.ajax({
    url: URL + "/get-data-by-time",
    type: "GET",
    success: function (data) {
      const listData = data;
      let dataset = listData.reduce((callback, item) => {
        const unixTimeStamp = item["time"] * 1000;
        let obj = {
          label: item["label"],
          hour: getHour(unixTimeStamp),
          date: getDate(unixTimeStamp),
          month: getMonth(unixTimeStamp) + 1,
          year: getYear(unixTimeStamp),
        };
        return [...callback, obj];
      }, []);
      const currentDate = new Date();
      const dataByYear = _.groupBy(dataset, "year");
      const dataCurrentYear = dataByYear[currentDate.getFullYear()];
      const dataByCurrentMonth = _.groupBy(dataset, "month")[
        currentDate.getMonth() + 1
      ];
      const dataByCurrentDate = _.groupBy(dataset, "date")[
        currentDate.getDate()
      ];
      const rs = getDataGroupByDate(dataByCurrentDate);
      drawChart2(rs);
    },
  });
}
function changeTimeByYear(pYear) {
  jQuery.ajax({
    url: URL + "/get-data-by-time",
    type: "GET",
    success: function (data) {
      const listData = data;
      let dataset = listData.reduce((callback, item) => {
        const unixTimeStamp = item["time"] * 1000;
        let obj = {
          label: item["label"],
          date: getDate(unixTimeStamp),
          month: getMonth(unixTimeStamp) + 1,
          year: getYear(unixTimeStamp),
        };
        return [...callback, obj];
      }, []);
      const dataByYear = _.groupBy(dataset, "year");
      const figure = getDataGroupByMonthAndYear(pYear, dataByYear);
      // console.log(figure)
      drawChart2(figure);
    },
  });
}

function changeTimeByMonth(pMonth, pYear) {
  jQuery.ajax({
    url: URL + "/get-data-by-time",
    type: "GET",
    success: function (data) {
      const listData = data;
      let dataset = listData.reduce((callback, item) => {
        const unixTimeStamp = item["time"] * 1000;
        let obj = {
          label: item["label"],
          date: getDate(unixTimeStamp),
          month: getMonth(unixTimeStamp) + 1,
          year: getYear(unixTimeStamp),
        };
        return [...callback, obj];
      }, []);
      const dataByYear = _.groupBy(dataset, "year");
      const figure = getDataGroupByMonth(pMonth, pYear, dataByYear);
      drawChart2(figure);
    },
  });
}
function callAPI2() {
  let response = [];
  jQuery.ajax({
    url: URL + "/get-data-by-time",
    type: "GET",
    success: function (data) {
      response.push(data);
    },
  });
  console.log(response);
  return response[0];
}
function drawChart2(figure) {
  const ctxLine = document.getElementById("myChart2");
  const CHART_COLORS = {
    red: "rgb(255, 99, 132)",
    orange: "rgb(255, 159, 64)",
    yellow: "rgb(255, 205, 86)",
    green: "rgb(75, 192, 192)",
    blue: "rgb(54, 162, 235)",
    purple: "rgb(153, 102, 255)",
    grey: "rgb(201, 203, 207)",
  };

  if (barChartCanvas2 !== undefined) {
    barChartCanvas2.destroy();
  }

  const labels = Object.keys(figure);
  const valuesOfData = Object.values(figure);
  const result = valuesOfData.reduce(
    (call, fun) => {
      let indexWith = fun["mask"];
      let indexWithout = fun["withoutMask"];

      return {
        with: [...call["with"], indexWith],
        without: [...call["without"], indexWithout],
      };
    },
    {
      with: [],
      without: [],
    }
  );
  const data = {
    labels: labels,
    datasets: [
      {
        label: "With Face Mask",
        data: result["with"],
        borderColor: CHART_COLORS.red,
        backgroundColor: "rgba(255, 99, 132, 0.5)",
      },
      {
        label: "Without Face Mask",
        data: result["without"],
        borderColor: CHART_COLORS.blue,
        backgroundColor: "rgba(54, 162, 235, 0.5)",
      },
    ],
  };

  barChartCanvas2 = new Chart(ctxLine, {
    type: "line",
    data: data,
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "top",
        },
        title: {
          display: true,
          text: "Line chart with mask and without mark",
        },
      },
    },
  });
}
function getDataGroupByDate(dataByDate) {
  const dataGroupByHour = _.groupBy(dataByDate, "hour");
  let response = {};
  for (let i = 0; i <= 23; i++) {
    let data = dataGroupByHour[i.toString()];
    let indexWithMark = 0;
    let indexWithoutMark = 0;
    if (data != undefined) {
      for (let j = 0; j < data.length; j++) {
        if (data[j]["label"] == "without_mask") {
          indexWithoutMark++;
        } else {
          if (data[j]["label"] == "with_mask") {
            indexWithMark++;
          }
        }
      }
    }
    result = {
      mask: indexWithMark,
      withoutMask: indexWithoutMark,
    };
    let key = i.toString() + " Giờ";
    response[key] = result;
  }
  return response;
}

function getDataGroupByMonthAndYear(paramYear, dataByYear) {
  const dataGroupByYear = _.groupBy(dataByYear[paramYear], "month");
  let response = {};
  for (let i = 1; i <= 12; i++) {
    let data = dataGroupByYear[i.toString()];
    let indexWithMark = 0;
    let indexWithoutMark = 0;
    if (data != undefined) {
      for (let j = 0; j < data.length; j++) {
        if (data[j]["label"] == "without_mask") {
          indexWithoutMark++;
        } else {
          if (data[j]["label"] == "with_mask") {
            indexWithMark++;
          }
        }
      }
    }
    result = {
      mask: indexWithMark,
      withoutMask: indexWithoutMark,
    };
    let key = "Tháng " + i.toString();
    response[key] = result;
  }
  return response;
}
function getDataGroupByMonth(paramMonth, paramYear, dataByYear) {
  const dataGroupByYear = _.groupBy(dataByYear[paramYear], "month");
  let response = {};
  let dataRoot = dataGroupByYear[paramMonth.toString()];
  let dateNew = _.groupBy(dataRoot, "date");
  const numberDaysOfMonth = getDaysInMonth(paramYear, paramMonth);
  for (let i = 1; i <= numberDaysOfMonth; i++) {
    let data = dateNew[i.toString()];
    let indexWithMark = 0;
    let indexWithoutMark = 0;
    if (data != undefined) {
      for (let j = 0; j < data.length; j++) {
        if (data[j]["label"] === "without_mask") {
          indexWithoutMark++;
        } else {
          if (data[j]["label"] === "with_mask") {
            indexWithMark++;
          }
        }
      }
    }
    result = {
      mask: indexWithMark,
      withoutMask: indexWithoutMark,
    };
    let key = "Ngày " + i.toString();
    response[key] = result;
  }
  return response;
}
function getDaysInMonth(year, month) {
  return new Date(year, month, 0).getDate();
}
