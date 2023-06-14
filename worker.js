const DATA_URL =
    'https://raw.githubusercontent.com/noc7c9/pokeapi.sqlite/dist/pokeapi.sqlite.gz';

const SQLJS = 'https://cdn.jsdelivr.net/npm/sql.js@1.8.0/dist';
importScripts(`${SQLJS}/sql-wasm.js`);

const sqlP = initSqlJs({ locateFile: (file) => `${SQLJS}/${file}` });
const data = fetch(DATA_URL).then(async (res) => {
    const stream = res.body.pipeThrough(new DecompressionStream('gzip'));
    return new Uint8Array(await new Response(stream).arrayBuffer());
});

let db;
const getDb = async () => {
    if (db == null) {
        const sql = await sqlP;
        db = new sql.Database(await data);
    }
    return db;
};

onmessage = async function (e) {
    const db = await getDb();

    const { id, fn, args } = e.data;

    if (fn === 'run') {
        db.run(...args);
        return postMessage({ id });
    }

    if (fn === 'exec') {
        const result = db.exec(...args);
        return postMessage({ id, result });
    }

    throw new Error(`Unknown function: ${fn}`);
};
