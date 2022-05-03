from aiosqlite import connect
from os import getenv

class Plugin:
    def __init__(self, *args) -> None:
        self.artifact = args[0]
        self.version = args[1]
        self.pending = args[2]
        self.author = args[3]
        self.description = args[4]
        self.tags = args[5].split(",") if type(args[5]) == str else args[5]
        self.hash = args[6]
    
    def __dict__(self):
        return {
            "artifact": self.artifact,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "tags": self.tags,
            "hash": self.hash
        }

async def Database():
    conn = await connect(getenv("DB_PATH", "plugin_store.db"))
    queries = ["""
        CREATE TABLE IF NOT EXISTS "plugins" (
            "artifact"	TEXT NOT NULL,
            "version"	TEXT NOT NULL,
            "pending"	INTEGER NOT NULL DEFAULT 1,
            "author"	TEXT,
            "description"	TEXT,
            "tags"	TEXT,
            "hash"  TEXT
        );
    """,
    """
        CREATE TABLE IF NOT EXISTS "approvers" (
            "id"       TEXT NOT NULL,
            "added_by" TEXT NOT NULL
        );
    """]
    for q in queries:
        await conn.execute(q)
    await conn.commit()
    return _Database(conn)

class _Database:
    def __init__(self, db) -> None:
        self.db = db

    async def add_approver(self, id, added_by):
        await self.db.execute("INSERT INTO approvers(id, added_by) values(?, ?)", (id, added_by,))
        await self.db.commit()
        
    async def remove_approver(self, id):
        await self.db.execute("DELETE FROM approvers WHERE id = ?", (id,))
        await self.db.commit()
    
    async def is_approver(self, id):
        cursor = await self.db.execute("SELECT id FROM approvers")
        rows = [i[0] for i in (await cursor.fetchall())]
        return id in rows

    async def insert_plugin(self, plugin):
        await self.db.execute("""
        INSERT INTO plugins(artifact, version, author, description, tags, hash) 
        VALUES(?, ?, ?, ?, ?, ?)
        """, (plugin.artifact, plugin.version, plugin.author, plugin.description, ",".join(plugin.tags), plugin.hash,))

    async def set_pending(self, artifact, version, pending):
        await self.db.execute("""
        UPDATE plugins SET pending = ? WHERE artifact = ? AND version = ?
        """, (pending, artifact, version,))
        await self.db.commit()

    async def remove_plugin(self, artifact, version):
        await self.db.execute("DELETE FROM plugins WHERE artifact = ? AND version = ?", (artifact, version,))
        await self.db.commit()

    async def get_plugins(self, pending=0):
        cursor = await self.db.execute("SELECT * FROM plugins WHERE pending = ?", (pending,))
        rows = await cursor.fetchall()
        return [Plugin(*i) for i in rows]
    
    async def search(self, query="", tags=[]):
        if not query and not tags:
            return await self.get_plugins()
        query_string = "SELECT * FROM plugins WHERE pending = 0 AND "
        params = []
        _and = False
        if query:
            query_string += "artifact LIKE ? "
            _and = True
            params.append("%{}%".format(query))
        if tags:
            if _and:
                query_string += "AND "
            for i,v in enumerate(tags):
                query_string += "tags LIKE ? " + ("AND " if i < len(tags)-1 else "")
                params.append("%{}%".format(v))
        cursor = await self.db.execute(query_string, tuple(params))
        rows = await cursor.fetchall()
        return [Plugin(*i) for i in rows]
