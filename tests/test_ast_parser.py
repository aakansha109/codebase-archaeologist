from pathlib import Path
from archaeologist.ingest.ast_parser import ASTCodeParser

def test_python_ast_parsing(tmp_path: Path):
    sample_py = tmp_path / "sample.py"
    sample_py.write_text('''
def calculate_tax(amount: float) -> float:
    """Calculates standard tax rate."""
    return amount * 0.15

class AuthService:
    """Handles authentication."""
    def login(self, user: str):
        return True
''')
    
    parser = ASTCodeParser()
    chunks = parser.parse_file(sample_py, relative_to=tmp_path)
    
    names = [c.name for c in chunks]
    assert "calculate_tax" in names
    assert "AuthService" in names
    assert "AuthService.login" in names
    
    # Check docstrings & line boundaries
    tax_chunk = next(c for c in chunks if c.name == "calculate_tax")
    assert tax_chunk.docstring == "Calculates standard tax rate."
    assert tax_chunk.start_line == 2
    assert tax_chunk.end_line == 4

def test_javascript_typescript_parsing(tmp_path: Path):
    sample_ts = tmp_path / "auth.ts"
    sample_ts.write_text('''
export interface UserSession {
    token: string;
    expiresAt: number;
}

export type SafeUser = {
    id: string;
    email: string;
};

export function authenticateUser(token: string) {
    if (!token) return false;
    return verifyToken(token);
}

export class RedisCache {
    connect() {
        return true;
    }
}
''')
    parser = ASTCodeParser()
    chunks = parser.parse_file(sample_ts, relative_to=tmp_path)
    names = [c.name for c in chunks]
    assert "UserSession" in names
    assert "SafeUser" in names
    assert "authenticateUser" in names
    assert "RedisCache" in names
    
    # Check start and end lines
    session_chunk = next(c for c in chunks if c.name == "UserSession")
    assert session_chunk.chunk_type == "interface"
    assert session_chunk.start_line == 2
    assert session_chunk.end_line == 5

def test_go_parsing(tmp_path: Path):
    sample_go = tmp_path / "auth.go"
    sample_go.write_text('''
package main

type Config struct {
    Port int
    Host string
}

func (c *Config) GetAddress() string {
    return c.Host + ":" + string(c.Port)
}

func StartServer(cfg Config) error {
    return nil
}
''')
    parser = ASTCodeParser()
    chunks = parser.parse_file(sample_go, relative_to=tmp_path)
    names = [c.name for c in chunks]
    assert "Config" in names
    assert "GetAddress" in names
    assert "StartServer" in names
    
    func_chunk = next(c for c in chunks if c.name == "StartServer")
    assert func_chunk.chunk_type == "function"
    assert func_chunk.start_line == 13
    assert func_chunk.end_line == 15

def test_rust_parsing(tmp_path: Path):
    sample_rs = tmp_path / "auth.rs"
    sample_rs.write_text('''
pub struct Connection {
    pub ip: String,
}

pub trait Database {
    fn query(&self, sql: &str) -> Result<(), Error>;
}

impl Database for Connection {
    fn query(&self, sql: &str) -> Result<(), Error> {
        Ok(())
    }
}

pub async fn run_migration() {
    println!("Migrated!");
}
''')
    parser = ASTCodeParser()
    chunks = parser.parse_file(sample_rs, relative_to=tmp_path)
    names = [c.name for c in chunks]
    assert "Connection" in names
    assert "Database" in names
    assert "run_migration" in names
    
    struct_chunk = next(c for c in chunks if c.name == "Connection")
    assert struct_chunk.chunk_type == "struct"
    assert struct_chunk.start_line == 2
    assert struct_chunk.end_line == 4
