/* Optional progressive enhancement: public display data only, no API credentials. */
(() => {
  'use strict';
  const element = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const card = (item, kind) => {
    const article = element('article', 'card');
    const label = kind === 'episodes' ? 'Episode' : 'Movie';
    if (!item) {
      article.classList.add('empty');
      article.append(element('span', 'label', label), element('p', '', 'No watch history yet.'));
      return article;
    }
    const watched = new Date(item.watched_at);
    if (typeof item.title !== 'string' || !item.title.trim() ||
        typeof item.watched_at !== 'string' || Number.isNaN(watched.getTime())) {
      throw new Error('Invalid watch history');
    }
    let art = element('div', 'poster placeholder', '▶');
    art.setAttribute('aria-hidden', 'true');
    if (typeof item.poster === 'string' && /^https:\/\/image\.tmdb\.org\/t\/p\/w200\/[a-zA-Z0-9_.-]+$/.test(item.poster)) {
      const image = element('img', 'poster');
      image.src = item.poster;
      image.alt = '';
      image.width = 80;
      image.height = 120;
      image.loading = 'lazy';
      const placeholder = art;
      image.addEventListener('error', () => image.replaceWith(placeholder), {once: true});
      art = image;
    }
    const details = element('div', 'details');
    let subtitle = item.year ? String(item.year) : '';
    if (kind === 'episodes') {
      const code = Number.isInteger(item.season) && Number.isInteger(item.number)
        ? `S${String(item.season).padStart(2, '0')}E${String(item.number).padStart(2, '0')}` : '';
      subtitle = [code, typeof item.episode === 'string' ? item.episode : ''].filter(Boolean).join(' · ');
    }
    const dayOnly = item.date_precision === 'day';
    const dateOptions = dayOnly ? {day:'numeric', month:'short', year:'numeric', timeZone:'UTC'}
      : {day:'numeric', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit', timeZoneName:'short'};
    const time = element('time', '', `Watched ${new Intl.DateTimeFormat(undefined, dateOptions).format(watched)}`);
    time.dateTime = dayOnly ? item.watched_at : watched.toISOString();
    details.append(element('span', 'label', label), element('h2', '', item.title), element('p', '', subtitle), time);
    article.append(art, details);
    return article;
  };
  document.querySelectorAll('[data-trakt-feed]').forEach(async widget => {
    const target = widget.querySelector('.trakt-cards');
    const status = widget.querySelector('.trakt-status');
    if (!target) return;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(widget.dataset.traktFeed, {signal: controller.signal, credentials: 'omit'});
      if (!response.ok) throw new Error('Feed unavailable');
      const data = await response.json();
      if (data.version !== 1 || !Array.isArray(data.items) || data.items.length > 2 ||
          data.items.some(item => !item || !['episodes', 'movies'].includes(item.type)) ||
          new Set(data.items.map(item => item.type)).size !== data.items.length) throw new Error('Invalid feed');
      const cards = ['episodes', 'movies'].map(kind => card(data.items.find(item => item.type === kind), kind));
      target.replaceChildren(...cards);
      if (status) status.textContent = '';
    } catch (_) {
      if (status) status.textContent = 'Showing the last saved watch history. ';
    } finally {
      clearTimeout(timeout);
    }
  });
})();
