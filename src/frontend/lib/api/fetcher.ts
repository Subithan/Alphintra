export const coinfetcher = (url: string) =>
  fetch(url, {
    method: "GET",
    headers: { accept: "application/json" },
  }).then((res) => res.json());

  // utils/fetcher.ts
export const newsFetcher = (url: string) =>
  fetch(url, {
    method: 'GET',
    headers: { accept: 'application/json' },
  }).then((res) => res.json());