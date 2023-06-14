window.db = (() => {
    const worker = new Worker('./worker.js');
    const requests = new Map();
    let nextId = 0;
    worker.addEventListener('message', (e) => {
        const { id, result } = e.data;
        const resolve = requests.get(id);
        resolve(result);
    });
    const method =
        (fn) =>
        (...args) => {
            const id = nextId++;
            const promise = new Promise((resolve) => requests.set(id, resolve));
            worker.postMessage({ id, fn, args });
            return promise;
        };
    return {
        run: method('run'),
        exec: method('exec'),
    };
})();

async function listTables() {
    const [rows] = await db.exec(
        'SELECT name FROM sqlite_master WHERE type="table";',
    );
    console.log('listTables', rows);
    return rows.values;
}

function pretty(value) {
    return JSON.stringify(value, null, 4);
}
