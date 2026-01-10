-- Seven Ultimate Productivity Database Schema
-- Simple SQLite database for conversation search and basic CRM

-- Main conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,           -- 'chatgpt' or 'claude'
    title TEXT,
    content TEXT NOT NULL,
    created_at TEXT,
    file_path TEXT,                 -- Original export file path
    imported_at TEXT DEFAULT (datetime('now')),
    word_count INTEGER,
    participants TEXT               -- JSON array of participants if available
);

-- Basic contact/CRM tracking
CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    company TEXT,
    deal_value REAL,
    currency TEXT DEFAULT 'DKK',
    status TEXT DEFAULT 'cold',     -- 'cold', 'warm', 'proposal', 'won', 'lost'
    github_issue INTEGER,           -- Link to GitHub issue number
    linkedin_url TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- GitHub issues tracking (synced from GitHub)
CREATE TABLE IF NOT EXISTS github_issues (
    id INTEGER PRIMARY KEY,         -- GitHub issue number
    title TEXT NOT NULL,
    body TEXT,
    status TEXT,                    -- 'open' or 'closed'
    labels TEXT,                    -- JSON array of labels
    created_at TEXT,
    updated_at TEXT,
    github_url TEXT,
    contact_id TEXT,                -- Link to contacts table
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

-- Simple task/follow-up tracking
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    due_date TEXT,
    completed_at TEXT,
    contact_id TEXT,
    github_issue INTEGER,
    task_type TEXT,                 -- 'email', 'call', 'follow-up', 'reminder'
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (contact_id) REFERENCES contacts(id),
    FOREIGN KEY (github_issue) REFERENCES github_issues(id)
);

-- Full-text search for conversations (fast search without vectors)
CREATE VIRTUAL TABLE IF NOT EXISTS conversations_fts USING fts5(
    title, 
    content, 
    content='conversations',
    content_rowid='rowid'
);

-- Populate FTS table with existing data
INSERT INTO conversations_fts(rowid, title, content) 
SELECT rowid, title, content FROM conversations;

-- Trigger to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS conversations_ai AFTER INSERT ON conversations BEGIN
    INSERT INTO conversations_fts(rowid, title, content) VALUES (new.rowid, new.title, new.content);
END;

CREATE TRIGGER IF NOT EXISTS conversations_ad AFTER DELETE ON conversations BEGIN
    INSERT INTO conversations_fts(conversations_fts, rowid, title, content) VALUES('delete', old.rowid, old.title, old.content);
END;

CREATE TRIGGER IF NOT EXISTS conversations_au AFTER UPDATE ON conversations BEGIN
    INSERT INTO conversations_fts(conversations_fts, rowid, title, content) VALUES('delete', old.rowid, old.title, old.content);
    INSERT INTO conversations_fts(rowid, title, content) VALUES (new.rowid, new.title, new.content);
END;

-- Useful indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_source ON conversations(source);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_contacts_status ON contacts(status);
CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company);
CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_github_issues_status ON github_issues(status);

-- Helper view for contact pipeline
CREATE VIEW IF NOT EXISTS contact_pipeline AS
SELECT 
    c.*,
    gi.title as issue_title,
    gi.github_url,
    COUNT(t.id) as task_count,
    MAX(t.due_date) as next_task_due
FROM contacts c
LEFT JOIN github_issues gi ON gi.contact_id = c.id
LEFT JOIN tasks t ON t.contact_id = c.id AND t.completed_at IS NULL
GROUP BY c.id;

-- Sample data for testing
INSERT OR IGNORE INTO contacts (id, name, company, status, deal_value) VALUES 
('test-1', 'Test Contact', 'Test Company', 'warm', 15000),
('test-2', 'John Doe', 'Example Corp', 'proposal', 25000);

-- Database metadata
CREATE TABLE IF NOT EXISTS db_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

INSERT OR REPLACE INTO db_metadata (key, value) VALUES 
('schema_version', '1.0'),
('created_at', datetime('now')),
('description', 'Seven Ultimate Productivity Database');