

from(bucket: "example_bucket")
  |> range(start: -1d)
  |> filter(fn: (r) => r._measurement == "heart_rate")
  |> filter(fn: (r) => r._field == "smoothed" or r._field == "original_time")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> window(every: 10h) 
  |> map(fn: (r) => ({
      _time: time(v: r.original_time),  
      smoothed: r.smoothed
  }))

