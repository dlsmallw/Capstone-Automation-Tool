CREATE TABLE IF NOT EXISTS sites (
    id INTEGER,
    site_name TEXT NOT NULL,
    username TEXT,
    user_pwd TEXT,
    site_token TEXT,
    PRIMARY KEY(id AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS taiga_projects (
    id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    project_owner TEXT NOT NULL,
    is_selected BOOLEAN NOT NULL CHECK (is_complete IN (0, 1)),
    PRIMARY KEY(id)
);

CREATE TABLE IF NOT EXISTS repos (
    id INTEGER,
    repo_name TEXT NOT NULL,
    owner_uid TEXT NOT NULL,
    repo_site_id Integer NOT NULL,
    PRIMARY KEY(id AUTOINCREMENT),
    FOREIGN KEY(repo_site_id) REFERENCES repo_sites(id)
);

CREATE TABLE IF NOT EXISTS members (
    id INTEGER,
    username TEXT NOT NULL,
    alt_alias TEXT,
    PRIMARY KEY(username)
);

CREATE TABLE IF NOT EXISTS sprints (
    id INTEGER,
    sprint_name TEXT NOT NULL,
    sprint_start INTEGER,
    sprint_end INTEGER,
    PRIMARY KEY(id AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS userstories (
    id INTEGER,
    us_num INTEGER NOT NULL,
    is_complete BOOLEAN NOT NULL CHECK (is_complete IN (0, 1)),
    sprint_id INTEGER,
    points INTEGER NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY(sprint_id) REFERENCES sprints(id)
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER,
    task_num INTEGER NOT NULL,
    is_complete BOOLEAN NOT NULL CHECK (is_complete IN (0, 1)),
    us_id INTEGER,
    assignee TEXT,
    task_subject TEXT,
    PRIMARY KEY(id),
    FOREIGN KEY(us_id) REFERENCES userstories(id),
    FOREIGN KEY(assignee) REFERENCES members(username)
);

CREATE TABLE IF NOT EXISTS commits (
    id INTEGER,
    repo_id INTEGER,
    az_date INTEGER NOT NULL,
    utc_datetime INTEGER NOT NULL,
    commit_message TEXT,
    task_id INTEGER,
    author TEXT,
    commit_url TEXT NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY(task_id) REFERENCES tasks(id),
    FOREIGN KEY(author) REFERENCES members(username)
);

INSERT INTO sites VALUES(NULL, 'Taiga', NULL, NULL, NULL);
INSERT INTO sites VALUES(NULL, 'GitHub', NULL, NULL, NULL);
INSERT INTO sites VALUES(NULL, 'GitLab', NULL, NULL, NULL);