// Workshop collections for the /workshops/ area of the site.
//
// The collection index files live in each workshop repository on GitHub and
// are downloaded fresh every time the site is built, so the pages always
// reflect the current state of the repositories. Nothing is cached or
// committed. If a download fails the build fails, which leaves the
// previously deployed site in place.

const GITHUB_OWNER = 'GrahamDumpleton';
const BRANCH = 'main';

// Each group is one repository and gets one page. A repository with a
// catalog.json can hold several collections; otherwise it has a single
// collection.json at its root. Launch links open the whole repository.
// Where the workshops teach a package of their own, project links to it.
const GROUPS = [
    {
        slug: 'python-decorators',
        repo: 'decorator-workshops',
        index: 'collection.json',
        icon: 'bi-at',
        jupyterlite: 'https://grahamdumpleton.github.io/decorator-workshops/lab/index.html',
    },
    {
        slug: 'wrapt',
        repo: 'wrapt-workshops',
        index: 'catalog.json',
        icon: 'bi-box-seam',
        project: { name: 'wrapt', url: 'https://github.com/GrahamDumpleton/wrapt' },
    },
    {
        slug: 'wrapture',
        repo: 'wrapture-workshops',
        index: 'collection.json',
        icon: 'bi-activity',
        project: { name: 'wrapture', url: 'https://github.com/GrahamDumpleton/wrapture' },
    },
];

function rawUrl(repo, file) {
    return `https://raw.githubusercontent.com/${GITHUB_OWNER}/${repo}/${BRANCH}/${file}`;
}

async function fetchJson(url) {
    const response = await fetch(url, { signal: AbortSignal.timeout(30000) });
    if (!response.ok) {
        throw new Error(`Failed to download ${url}: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

// Durations are given like "15m", "1h" or "1h30m". Returns minutes.
function parseMinutes(duration) {
    if (!duration) return 0;
    const match = String(duration).match(/^\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*$/i);
    if (!match) return 0;
    return (parseInt(match[1] || '0', 10) * 60) + parseInt(match[2] || '0', 10);
}

function formatMinutes(minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours && mins) return `${hours}h ${mins}m`;
    if (hours) return `${hours}h`;
    return `${mins}m`;
}

// Tags every workshop in a collection shares say nothing about an individual
// workshop, so they are dropped from the per-workshop tag list.
function normaliseCollection(data) {
    const workshops = data.workshops || [];
    const common = workshops.length > 1
        ? (workshops[0].tags || []).filter(tag => workshops.every(w => (w.tags || []).includes(tag)))
        : [];

    const items = workshops.map((w, i) => ({
        number: i + 1,
        name: w.name,
        title: w.title,
        description: w.description,
        duration: w.duration,
        minutes: parseMinutes(w.duration),
        tags: (w.tags || []).filter(tag => !common.includes(tag)),
        jupyterlite: (w.frontends || []).includes('jupyterlite'),
    }));

    const minutes = items.reduce((sum, w) => sum + w.minutes, 0);

    return {
        id: data.id,
        title: data.title,
        description: data.description,
        tags: data.tags || common,
        workshops: items,
        count: items.length,
        minutes,
        total_time: formatMinutes(minutes),
    };
}

async function loadGroup(group) {
    const index = await fetchJson(rawUrl(group.repo, group.index));

    let collections;
    if (Array.isArray(index.collections)) {
        collections = await Promise.all(index.collections.map(async entry => {
            const data = await fetchJson(rawUrl(group.repo, entry.url));
            return normaliseCollection({ ...data, tags: data.tags || entry.tags });
        }));
    } else {
        collections = [normaliseCollection(index)];
    }

    const count = collections.reduce((sum, c) => sum + c.count, 0);
    const minutes = collections.reduce((sum, c) => sum + c.minutes, 0);
    const repoUrl = `https://github.com/${GITHUB_OWNER}/${group.repo}`;

    return {
        slug: group.slug,
        icon: group.icon,
        title: index.title,
        description: index.description,
        repo_url: repoUrl,
        project: group.project || null,
        launch: {
            jupyterlite: group.jupyterlite || null,
            binder: `https://mybinder.org/v2/gh/${GITHUB_OWNER}/${group.repo}/${BRANCH}?urlpath=lab`,
            codespaces: `https://codespaces.new/${GITHUB_OWNER}/${group.repo}?quickstart=1`,
        },
        collections,
        count,
        minutes,
        total_time: formatMinutes(minutes),
    };
}

module.exports = async function() {
    const groups = await Promise.all(GROUPS.map(loadGroup));
    return { groups };
};
