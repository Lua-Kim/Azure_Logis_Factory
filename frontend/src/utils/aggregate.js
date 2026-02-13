const clampSeries = (items, maxPoints) => {
  if (!maxPoints || items.length <= maxPoints) {
    return items;
  }
  return items.slice(items.length - maxPoints);
};

const aggregateByKey = (items, keyFn, valueFn) => {
  const map = new Map();
  items.forEach((item) => {
    const key = keyFn(item);
    if (key === null || key === undefined) {
      return;
    }
    const current = map.get(key) || { key, total: 0, count: 0 };
    current.total += valueFn(item);
    current.count += 1;
    map.set(key, current);
  });
  return Array.from(map.values());
};

const aggregateKpiSeries = (items, maxPoints = 24) => {
  const buckets = aggregateByKey(
    items,
    (item) => item.window_end,
    (item) => item.throughput_count || 0
  )
    .map((bucket) => ({
      time: new Date(bucket.key),
      throughput: bucket.total
    }))
    .sort((a, b) => a.time - b.time);

  return clampSeries(
    buckets.map((bucket) => ({
      timeLabel: bucket.time.toLocaleTimeString(),
      throughput: bucket.throughput
    })),
    maxPoints
  );
};

const aggregateKpiByLine = (items) =>
  aggregateByKey(
    items,
    (item) => item.line_id,
    (item) => item.throughput_count || 0
  ).map((bucket) => ({
    line: bucket.key,
    throughput: bucket.total,
    average: bucket.count ? bucket.total / bucket.count : 0,
    count: bucket.count
  }));

const aggregateBottleneckByCause = (items, limit = 6) => {
  const grouped = aggregateByKey(
    items,
    (item) => item.cause_code || "UNKNOWN",
    () => 1
  ).sort((a, b) => b.total - a.total);

  if (grouped.length <= limit) {
    return grouped.map((bucket) => ({ name: bucket.key, value: bucket.total }));
  }

  const head = grouped.slice(0, limit - 1);
  const tail = grouped.slice(limit - 1);
  const otherTotal = tail.reduce((sum, bucket) => sum + bucket.total, 0);

  return [
    ...head.map((bucket) => ({ name: bucket.key, value: bucket.total })),
    { name: "OTHER", value: otherTotal }
  ];
};

const aggregateBottleneckDurationByLine = (items, limit = 8) =>
  aggregateByKey(
    items,
    (item) => item.line_id || "-",
    (item) => item.duration_sec || 0
  )
    .map((bucket) => ({
      line: bucket.key,
      duration: bucket.total,
      count: bucket.count
    }))
    .sort((a, b) => b.duration - a.duration)
    .slice(0, limit);

const aggregateEventsByHour = (items) => {
  const buckets = aggregateByKey(
    items,
    (item) => {
      if (!item.occurred_at) {
        return null;
      }
      const date = new Date(item.occurred_at);
      date.setMinutes(0, 0, 0);
      return date.toISOString();
    },
    () => 1
  )
    .map((bucket) => ({
      time: new Date(bucket.key),
      count: bucket.total
    }))
    .sort((a, b) => a.time - b.time);

  return buckets.map((bucket) => ({
    timeLabel: bucket.time.toLocaleString(),
    count: bucket.count
  }));
};

export {
  aggregateKpiSeries,
  aggregateKpiByLine,
  aggregateBottleneckByCause,
  aggregateBottleneckDurationByLine,
  aggregateEventsByHour
};
