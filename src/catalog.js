export function buildMediaUrl(mediaDirectory, relativePath) {
  const base = mediaDirectory.replace(/\/+$/, '');
  const path = relativePath.replace(/^\/+/, '');
  return `${base}/${path}`;
}

export function validateCatalog(items) {
  if (!Array.isArray(items)) throw new Error('片单必须是数组');
  const ids = new Set();
  for (const item of items) {
    if (!item?.id || !item?.title || !['movie', 'series'].includes(item.type) || ids.has(item.id)) {
      throw new Error('片单条目无效');
    }
    ids.add(item.id);
    if (item.type === 'movie' && typeof item.video !== 'string') throw new Error('电影缺少视频');
    if (item.type === 'series' && (!Array.isArray(item.episodes) || item.episodes.length === 0)) throw new Error('美剧缺少剧集');
    for (const episode of item.episodes ?? []) {
      if (!Number.isInteger(episode.season) || episode.season < 1 || !Number.isInteger(episode.episode) || episode.episode < 1 || typeof episode.video !== 'string') {
        throw new Error('剧集条目无效');
      }
    }
  }
  return items;
}

export function filterCatalog(items, activeType, query) {
  const normalizedQuery = query.trim().toLocaleLowerCase('zh-CN');
  return items.filter((item) => {
    const inActiveType = activeType === 'all' || item.type === activeType;
    return inActiveType && item.title.toLocaleLowerCase('zh-CN').includes(normalizedQuery);
  });
}

export function groupEpisodesBySeason(episodes) {
  const seasons = new Map();
  for (const episode of episodes) {
    seasons.set(episode.season, [...(seasons.get(episode.season) ?? []), episode]);
  }
  return [...seasons.entries()]
    .sort(([left], [right]) => left - right)
    .map(([season, seasonEpisodes]) => ({
      season,
      episodes: seasonEpisodes.sort((left, right) => left.episode - right.episode),
    }));
}

export function getPlayableSource(item, episode = null) {
  if (item.type === 'movie' && episode === null) return item.video;
  if (item.type === 'series' && episode !== null) return episode.video;
  throw new Error('请选择可播放的视频');
}
