create table tbl_status(
	id serial PRIMARY KEY,
	status_name varchar(50),
	status_code varchar(10),
	status_stage int
)

create table tbl_projects(
	id serial PRIMARY KEY,
	project_name varchar(50),
	status_id int references tbl_status(id)
)

create table tbl_users(
	id serial PRIMARY KEY,
	user_name varchar(100),
	login varchar(50),
	password varchar(50),
)

create table tbl_group(
	id serial PRIMARY KEY,
	group_name varchar(50),
	project_id int references tbl_projects(id) on delete cascade
)

create table tbl_groupdata(
	id serial PRIMARY KEY,
	user_id int references tbl_users(id) on delete cascade,
	group_id int references tbl_groups(id) on delete cascade
)

create table tbl_roles(
	id serial PRIMARY KEY,
	role_name varchar(50),
	role_code varchar(10),
	access_level int
)

create table tbl_userdata(
	id serial PRIMARY KEY,
	user_id int references tbl_users(id) on delete cascade,
	role_id int references tbl_roles(id),
	project_id int references tbl_projects(id) on delete CASCADE,
	de_completed bool,
	ce_completed bool,
	competence float
)

create table tbl_superiority(
	id serial PRIMARY KEY,
	superiority_name varchar(50),
	superiority_code int
)

create table tbl_nodes(
	id serial PRIMARY KEY,
	node_name varchar(100),
	uuid varchar(40),
	project_id int references tbl_projects(id) on delete cascade
)

create table tbl_edges(
	id serial PRIMARY KEY,
	uuid varchar(40),
	source_id int references tbl_nodes(id) on delete cascade,
	target_id int references tbl_nodes(id) on delete cascade,
	project_id int references tbl_projects(id) on delete cascade
)

create table tbl_edgedata(
	id serial PRIMARY KEY,
	competence float,
	deleted bool,
	edge_id int references tbl_edges(id) on delete cascade,
	user_id int references tbl_users(id) on delete cascade
)

create table tbl_compdata(
	id serial PRIMARY KEY,
	superior bool,
	superiority_id int references tbl_superiority(id),
	edgedata1_id int references tbl_edgedata(id) on delete cascade,
	edgedata2_id int references tbl_edgedata(id) on delete cascade
)