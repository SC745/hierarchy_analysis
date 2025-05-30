PGDMP      #                }         	   hierarchy    16.8    17.0 j    2           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false            3           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false            4           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false            5           1262    16584 	   hierarchy    DATABASE     o   CREATE DATABASE hierarchy WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'ru-RU';
    DROP DATABASE hierarchy;
                     postgres    false            �            1259    16585    tbl_compdata    TABLE     �   CREATE TABLE public.tbl_compdata (
    id integer NOT NULL,
    superior boolean,
    superiority_id integer,
    edgedata1_id integer,
    edgedata2_id integer
);
     DROP TABLE public.tbl_compdata;
       public         heap r       postgres    false            �            1259    16588    tbl_comparisondata_id_seq    SEQUENCE     �   CREATE SEQUENCE public.tbl_comparisondata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 0   DROP SEQUENCE public.tbl_comparisondata_id_seq;
       public               postgres    false    215            6           0    0    tbl_comparisondata_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.tbl_comparisondata_id_seq OWNED BY public.tbl_compdata.id;
          public               postgres    false    216            �            1259    16589    tbl_edgedata    TABLE     �   CREATE TABLE public.tbl_edgedata (
    id integer NOT NULL,
    competence double precision,
    deleted boolean,
    edge_id integer,
    user_id integer
);
     DROP TABLE public.tbl_edgedata;
       public         heap r       postgres    false            �            1259    16592    tbl_edgedata_id_seq    SEQUENCE     �   CREATE SEQUENCE public.tbl_edgedata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.tbl_edgedata_id_seq;
       public               postgres    false    217            7           0    0    tbl_edgedata_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.tbl_edgedata_id_seq OWNED BY public.tbl_edgedata.id;
          public               postgres    false    218            �            1259    16593 	   tbl_edges    TABLE     �   CREATE TABLE public.tbl_edges (
    id integer NOT NULL,
    source_id integer,
    target_id integer,
    project_id integer,
    uuid character varying(40)
);
    DROP TABLE public.tbl_edges;
       public         heap r       postgres    false            �            1259    16596    tbl_edges_id_seq    SEQUENCE     �   CREATE SEQUENCE public.tbl_edges_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.tbl_edges_id_seq;
       public               postgres    false    219            8           0    0    tbl_edges_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.tbl_edges_id_seq OWNED BY public.tbl_edges.id;
          public               postgres    false    220            �            1259    16597 	   tbl_users    TABLE     �   CREATE TABLE public.tbl_users (
    id integer NOT NULL,
    user_name character varying(100),
    login character varying(50),
    password character varying(25)
);
    DROP TABLE public.tbl_users;
       public         heap r       postgres    false            �            1259    16600    tbl_experts_id_seq    SEQUENCE     �   CREATE SEQUENCE public.tbl_experts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 )   DROP SEQUENCE public.tbl_experts_id_seq;
       public               postgres    false    221            9           0    0    tbl_experts_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.tbl_experts_id_seq OWNED BY public.tbl_users.id;
          public               postgres    false    222            �            1259    16601 
   tbl_groups    TABLE     z   CREATE TABLE public.tbl_groups (
    id integer NOT NULL,
    group_name character varying(50),
    project_id integer
);
    DROP TABLE public.tbl_groups;
       public         heap r       postgres    false            �            1259    16604    tbl_group_id_seq    SEQUENCE     �   CREATE SEQUENCE public.tbl_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.tbl_group_id_seq;
       public               postgres    false    223            :           0    0    tbl_group_id_seq    SEQUENCE OWNED BY     F   ALTER SEQUENCE public.tbl_group_id_seq OWNED BY public.tbl_groups.id;
          public               postgres    false    224            �            1259    16605    tbl_groupdata    TABLE     j   CREATE TABLE public.tbl_groupdata (
    id integer NOT NULL,
    user_id integer,
    group_id integer
);
 !   DROP TABLE public.tbl_groupdata;
       public         heap r       postgres    false            �            1259    16608    tbl_groupdata_id_seq    SEQUENCE     �   CREATE SEQUENCE public.tbl_groupdata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.tbl_groupdata_id_seq;
       public               postgres    false    225            ;           0    0    tbl_groupdata_id_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.tbl_groupdata_id_seq OWNED BY public.tbl_groupdata.id;
          public               postgres    false    226            �            1259    16609 	   tbl_nodes    TABLE     �   CREATE TABLE public.tbl_nodes (
    id integer NOT NULL,
    node_name character varying(100),
    project_id integer,
    uuid character varying(40)
);
    DROP TABLE public.tbl_nodes;
       public         heap r       postgres    false            �            1259    16612    tbl_nodes_id_seq    SEQUENCE     �   CREATE SEQUENCE public.tbl_nodes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.tbl_nodes_id_seq;
       public               postgres    false    227            <           0    0    tbl_nodes_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.tbl_nodes_id_seq OWNED BY public.tbl_nodes.id;
          public               postgres    false    228            �            1259    16613    tbl_projects    TABLE     �   CREATE TABLE public.tbl_projects (
    id integer NOT NULL,
    project_name character varying(50),
    status_id integer,
    merge_coef double precision,
    cons_coef double precision,
    incons_coef double precision,
    const_comp boolean
);
     DROP TABLE public.tbl_projects;
       public         heap r       postgres    false            �            1259    16616    tbl_projects_id_seq    SEQUENCE     �   CREATE SEQUENCE public.tbl_projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.tbl_projects_id_seq;
       public               postgres    false    229            =           0    0    tbl_projects_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.tbl_projects_id_seq OWNED BY public.tbl_projects.id;
          public               postgres    false    230            �            1259    16617 
   tbl_status    TABLE     �   CREATE TABLE public.tbl_status (
    id integer NOT NULL,
    status_name character varying(50),
    status_code character varying(10),
    status_stage integer
);
    DROP TABLE public.tbl_status;
       public         heap r       postgres    false            �            1259    16620    tbl_projectstatus_id_seq    SEQUENCE     �   CREATE SEQUENCE public.tbl_projectstatus_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 /   DROP SEQUENCE public.tbl_projectstatus_id_seq;
       public               postgres    false    231            >           0    0    tbl_projectstatus_id_seq    SEQUENCE OWNED BY     N   ALTER SEQUENCE public.tbl_projectstatus_id_seq OWNED BY public.tbl_status.id;
          public               postgres    false    232            �            1259    16621 	   tbl_roles    TABLE     �   CREATE TABLE public.tbl_roles (
    id integer NOT NULL,
    role_name character varying(50),
    role_code character varying(10),
    access_level integer
);
    DROP TABLE public.tbl_roles;
       public         heap r       postgres    false            �            1259    16624    tbl_roles_id_seq    SEQUENCE     �   CREATE SEQUENCE public.tbl_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.tbl_roles_id_seq;
       public               postgres    false    233            ?           0    0    tbl_roles_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.tbl_roles_id_seq OWNED BY public.tbl_roles.id;
          public               postgres    false    234            �            1259    16625    tbl_superiority    TABLE     �   CREATE TABLE public.tbl_superiority (
    id integer NOT NULL,
    superiority_name character varying(50),
    superiority_code integer
);
 #   DROP TABLE public.tbl_superiority;
       public         heap r       postgres    false            �            1259    16628    tbl_superiority_id_seq    SEQUENCE     �   CREATE SEQUENCE public.tbl_superiority_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.tbl_superiority_id_seq;
       public               postgres    false    235            @           0    0    tbl_superiority_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.tbl_superiority_id_seq OWNED BY public.tbl_superiority.id;
          public               postgres    false    236            �            1259    16629    tbl_userdata    TABLE     �   CREATE TABLE public.tbl_userdata (
    id integer NOT NULL,
    user_id integer,
    role_id integer,
    project_id integer,
    de_completed boolean,
    ce_completed boolean,
    competence double precision
);
     DROP TABLE public.tbl_userdata;
       public         heap r       postgres    false            �            1259    16632    tbl_userdata_id_seq    SEQUENCE     �   CREATE SEQUENCE public.tbl_userdata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.tbl_userdata_id_seq;
       public               postgres    false    237            A           0    0    tbl_userdata_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.tbl_userdata_id_seq OWNED BY public.tbl_userdata.id;
          public               postgres    false    238            Q           2604    16812    tbl_compdata id    DEFAULT     x   ALTER TABLE ONLY public.tbl_compdata ALTER COLUMN id SET DEFAULT nextval('public.tbl_comparisondata_id_seq'::regclass);
 >   ALTER TABLE public.tbl_compdata ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    216    215            R           2604    16813    tbl_edgedata id    DEFAULT     r   ALTER TABLE ONLY public.tbl_edgedata ALTER COLUMN id SET DEFAULT nextval('public.tbl_edgedata_id_seq'::regclass);
 >   ALTER TABLE public.tbl_edgedata ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    218    217            S           2604    16814    tbl_edges id    DEFAULT     l   ALTER TABLE ONLY public.tbl_edges ALTER COLUMN id SET DEFAULT nextval('public.tbl_edges_id_seq'::regclass);
 ;   ALTER TABLE public.tbl_edges ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    220    219            V           2604    16815    tbl_groupdata id    DEFAULT     t   ALTER TABLE ONLY public.tbl_groupdata ALTER COLUMN id SET DEFAULT nextval('public.tbl_groupdata_id_seq'::regclass);
 ?   ALTER TABLE public.tbl_groupdata ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    226    225            U           2604    16816    tbl_groups id    DEFAULT     m   ALTER TABLE ONLY public.tbl_groups ALTER COLUMN id SET DEFAULT nextval('public.tbl_group_id_seq'::regclass);
 <   ALTER TABLE public.tbl_groups ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    224    223            W           2604    16817    tbl_nodes id    DEFAULT     l   ALTER TABLE ONLY public.tbl_nodes ALTER COLUMN id SET DEFAULT nextval('public.tbl_nodes_id_seq'::regclass);
 ;   ALTER TABLE public.tbl_nodes ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    228    227            X           2604    16818    tbl_projects id    DEFAULT     r   ALTER TABLE ONLY public.tbl_projects ALTER COLUMN id SET DEFAULT nextval('public.tbl_projects_id_seq'::regclass);
 >   ALTER TABLE public.tbl_projects ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    230    229            Z           2604    16819    tbl_roles id    DEFAULT     l   ALTER TABLE ONLY public.tbl_roles ALTER COLUMN id SET DEFAULT nextval('public.tbl_roles_id_seq'::regclass);
 ;   ALTER TABLE public.tbl_roles ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    234    233            Y           2604    16820    tbl_status id    DEFAULT     u   ALTER TABLE ONLY public.tbl_status ALTER COLUMN id SET DEFAULT nextval('public.tbl_projectstatus_id_seq'::regclass);
 <   ALTER TABLE public.tbl_status ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    232    231            [           2604    16821    tbl_superiority id    DEFAULT     x   ALTER TABLE ONLY public.tbl_superiority ALTER COLUMN id SET DEFAULT nextval('public.tbl_superiority_id_seq'::regclass);
 A   ALTER TABLE public.tbl_superiority ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    236    235            \           2604    16822    tbl_userdata id    DEFAULT     r   ALTER TABLE ONLY public.tbl_userdata ALTER COLUMN id SET DEFAULT nextval('public.tbl_userdata_id_seq'::regclass);
 >   ALTER TABLE public.tbl_userdata ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    238    237            T           2604    16823    tbl_users id    DEFAULT     n   ALTER TABLE ONLY public.tbl_users ALTER COLUMN id SET DEFAULT nextval('public.tbl_experts_id_seq'::regclass);
 ;   ALTER TABLE public.tbl_users ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    222    221                      0    16585    tbl_compdata 
   TABLE DATA           `   COPY public.tbl_compdata (id, superior, superiority_id, edgedata1_id, edgedata2_id) FROM stdin;
    public               postgres    false    215   �                 0    16589    tbl_edgedata 
   TABLE DATA           Q   COPY public.tbl_edgedata (id, competence, deleted, edge_id, user_id) FROM stdin;
    public               postgres    false    217   �                 0    16593 	   tbl_edges 
   TABLE DATA           O   COPY public.tbl_edges (id, source_id, target_id, project_id, uuid) FROM stdin;
    public               postgres    false    219   �       "          0    16605    tbl_groupdata 
   TABLE DATA           >   COPY public.tbl_groupdata (id, user_id, group_id) FROM stdin;
    public               postgres    false    225   �                  0    16601 
   tbl_groups 
   TABLE DATA           @   COPY public.tbl_groups (id, group_name, project_id) FROM stdin;
    public               postgres    false    223   5�       $          0    16609 	   tbl_nodes 
   TABLE DATA           D   COPY public.tbl_nodes (id, node_name, project_id, uuid) FROM stdin;
    public               postgres    false    227   R�       &          0    16613    tbl_projects 
   TABLE DATA           s   COPY public.tbl_projects (id, project_name, status_id, merge_coef, cons_coef, incons_coef, const_comp) FROM stdin;
    public               postgres    false    229   o�       *          0    16621 	   tbl_roles 
   TABLE DATA           K   COPY public.tbl_roles (id, role_name, role_code, access_level) FROM stdin;
    public               postgres    false    233   ��       (          0    16617 
   tbl_status 
   TABLE DATA           P   COPY public.tbl_status (id, status_name, status_code, status_stage) FROM stdin;
    public               postgres    false    231    �       ,          0    16625    tbl_superiority 
   TABLE DATA           Q   COPY public.tbl_superiority (id, superiority_name, superiority_code) FROM stdin;
    public               postgres    false    235   ց       .          0    16629    tbl_userdata 
   TABLE DATA           p   COPY public.tbl_userdata (id, user_id, role_id, project_id, de_completed, ce_completed, competence) FROM stdin;
    public               postgres    false    237   f�                 0    16597 	   tbl_users 
   TABLE DATA           C   COPY public.tbl_users (id, user_name, login, password) FROM stdin;
    public               postgres    false    221   ��       B           0    0    tbl_comparisondata_id_seq    SEQUENCE SET     J   SELECT pg_catalog.setval('public.tbl_comparisondata_id_seq', 9379, true);
          public               postgres    false    216            C           0    0    tbl_edgedata_id_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('public.tbl_edgedata_id_seq', 3239, true);
          public               postgres    false    218            D           0    0    tbl_edges_id_seq    SEQUENCE SET     A   SELECT pg_catalog.setval('public.tbl_edges_id_seq', 3819, true);
          public               postgres    false    220            E           0    0    tbl_experts_id_seq    SEQUENCE SET     A   SELECT pg_catalog.setval('public.tbl_experts_id_seq', 10, true);
          public               postgres    false    222            F           0    0    tbl_group_id_seq    SEQUENCE SET     ?   SELECT pg_catalog.setval('public.tbl_group_id_seq', 29, true);
          public               postgres    false    224            G           0    0    tbl_groupdata_id_seq    SEQUENCE SET     C   SELECT pg_catalog.setval('public.tbl_groupdata_id_seq', 32, true);
          public               postgres    false    226            H           0    0    tbl_nodes_id_seq    SEQUENCE SET     A   SELECT pg_catalog.setval('public.tbl_nodes_id_seq', 1778, true);
          public               postgres    false    228            I           0    0    tbl_projects_id_seq    SEQUENCE SET     B   SELECT pg_catalog.setval('public.tbl_projects_id_seq', 19, true);
          public               postgres    false    230            J           0    0    tbl_projectstatus_id_seq    SEQUENCE SET     F   SELECT pg_catalog.setval('public.tbl_projectstatus_id_seq', 4, true);
          public               postgres    false    232            K           0    0    tbl_roles_id_seq    SEQUENCE SET     >   SELECT pg_catalog.setval('public.tbl_roles_id_seq', 4, true);
          public               postgres    false    234            L           0    0    tbl_superiority_id_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('public.tbl_superiority_id_seq', 9, true);
          public               postgres    false    236            M           0    0    tbl_userdata_id_seq    SEQUENCE SET     B   SELECT pg_catalog.setval('public.tbl_userdata_id_seq', 96, true);
          public               postgres    false    238            ^           2606    16646 $   tbl_compdata tbl_comparisondata_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.tbl_compdata
    ADD CONSTRAINT tbl_comparisondata_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.tbl_compdata DROP CONSTRAINT tbl_comparisondata_pkey;
       public                 postgres    false    215            `           2606    16648    tbl_edgedata tbl_edgedata_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.tbl_edgedata
    ADD CONSTRAINT tbl_edgedata_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.tbl_edgedata DROP CONSTRAINT tbl_edgedata_pkey;
       public                 postgres    false    217            b           2606    16650    tbl_edges tbl_edges_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.tbl_edges
    ADD CONSTRAINT tbl_edges_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.tbl_edges DROP CONSTRAINT tbl_edges_pkey;
       public                 postgres    false    219            d           2606    16652    tbl_edges tbl_edges_uuid_key 
   CONSTRAINT     W   ALTER TABLE ONLY public.tbl_edges
    ADD CONSTRAINT tbl_edges_uuid_key UNIQUE (uuid);
 F   ALTER TABLE ONLY public.tbl_edges DROP CONSTRAINT tbl_edges_uuid_key;
       public                 postgres    false    219            h           2606    16654    tbl_groups tbl_group_pkey 
   CONSTRAINT     W   ALTER TABLE ONLY public.tbl_groups
    ADD CONSTRAINT tbl_group_pkey PRIMARY KEY (id);
 C   ALTER TABLE ONLY public.tbl_groups DROP CONSTRAINT tbl_group_pkey;
       public                 postgres    false    223            j           2606    16656     tbl_groupdata tbl_groupdata_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.tbl_groupdata
    ADD CONSTRAINT tbl_groupdata_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.tbl_groupdata DROP CONSTRAINT tbl_groupdata_pkey;
       public                 postgres    false    225            l           2606    16658    tbl_nodes tbl_nodes_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.tbl_nodes
    ADD CONSTRAINT tbl_nodes_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.tbl_nodes DROP CONSTRAINT tbl_nodes_pkey;
       public                 postgres    false    227            n           2606    16660    tbl_nodes tbl_nodes_uuid_key 
   CONSTRAINT     W   ALTER TABLE ONLY public.tbl_nodes
    ADD CONSTRAINT tbl_nodes_uuid_key UNIQUE (uuid);
 F   ALTER TABLE ONLY public.tbl_nodes DROP CONSTRAINT tbl_nodes_uuid_key;
       public                 postgres    false    227            p           2606    16662    tbl_projects tbl_projects_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.tbl_projects
    ADD CONSTRAINT tbl_projects_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.tbl_projects DROP CONSTRAINT tbl_projects_pkey;
       public                 postgres    false    229            r           2606    16664 !   tbl_status tbl_projectstatus_pkey 
   CONSTRAINT     _   ALTER TABLE ONLY public.tbl_status
    ADD CONSTRAINT tbl_projectstatus_pkey PRIMARY KEY (id);
 K   ALTER TABLE ONLY public.tbl_status DROP CONSTRAINT tbl_projectstatus_pkey;
       public                 postgres    false    231            t           2606    16666    tbl_roles tbl_roles_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.tbl_roles
    ADD CONSTRAINT tbl_roles_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.tbl_roles DROP CONSTRAINT tbl_roles_pkey;
       public                 postgres    false    233            v           2606    16668 $   tbl_superiority tbl_superiority_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.tbl_superiority
    ADD CONSTRAINT tbl_superiority_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.tbl_superiority DROP CONSTRAINT tbl_superiority_pkey;
       public                 postgres    false    235            x           2606    16670    tbl_userdata tbl_userdata_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.tbl_userdata
    ADD CONSTRAINT tbl_userdata_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.tbl_userdata DROP CONSTRAINT tbl_userdata_pkey;
       public                 postgres    false    237            f           2606    16672    tbl_users tbl_users_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.tbl_users
    ADD CONSTRAINT tbl_users_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.tbl_users DROP CONSTRAINT tbl_users_pkey;
       public                 postgres    false    221            y           2606    16673 +   tbl_compdata tbl_compdata_edgedata1_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_compdata
    ADD CONSTRAINT tbl_compdata_edgedata1_id_fkey FOREIGN KEY (edgedata1_id) REFERENCES public.tbl_edgedata(id) ON DELETE CASCADE;
 U   ALTER TABLE ONLY public.tbl_compdata DROP CONSTRAINT tbl_compdata_edgedata1_id_fkey;
       public               postgres    false    217    4704    215            z           2606    16678 +   tbl_compdata tbl_compdata_edgedata2_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_compdata
    ADD CONSTRAINT tbl_compdata_edgedata2_id_fkey FOREIGN KEY (edgedata2_id) REFERENCES public.tbl_edgedata(id) ON DELETE CASCADE;
 U   ALTER TABLE ONLY public.tbl_compdata DROP CONSTRAINT tbl_compdata_edgedata2_id_fkey;
       public               postgres    false    217    215    4704            {           2606    16683 -   tbl_compdata tbl_compdata_superiority_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_compdata
    ADD CONSTRAINT tbl_compdata_superiority_id_fkey FOREIGN KEY (superiority_id) REFERENCES public.tbl_superiority(id);
 W   ALTER TABLE ONLY public.tbl_compdata DROP CONSTRAINT tbl_compdata_superiority_id_fkey;
       public               postgres    false    215    4726    235            |           2606    16688 &   tbl_edgedata tbl_edgedata_edge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_edgedata
    ADD CONSTRAINT tbl_edgedata_edge_id_fkey FOREIGN KEY (edge_id) REFERENCES public.tbl_edges(id) ON DELETE CASCADE;
 P   ALTER TABLE ONLY public.tbl_edgedata DROP CONSTRAINT tbl_edgedata_edge_id_fkey;
       public               postgres    false    217    219    4706            }           2606    16693 &   tbl_edgedata tbl_edgedata_user_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_edgedata
    ADD CONSTRAINT tbl_edgedata_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.tbl_users(id);
 P   ALTER TABLE ONLY public.tbl_edgedata DROP CONSTRAINT tbl_edgedata_user_id_fkey;
       public               postgres    false    221    4710    217            ~           2606    16698 #   tbl_edges tbl_edges_project_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_edges
    ADD CONSTRAINT tbl_edges_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.tbl_projects(id) ON DELETE CASCADE;
 M   ALTER TABLE ONLY public.tbl_edges DROP CONSTRAINT tbl_edges_project_id_fkey;
       public               postgres    false    229    219    4720                       2606    16703 "   tbl_edges tbl_edges_source_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_edges
    ADD CONSTRAINT tbl_edges_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.tbl_nodes(id) ON DELETE CASCADE;
 L   ALTER TABLE ONLY public.tbl_edges DROP CONSTRAINT tbl_edges_source_id_fkey;
       public               postgres    false    219    227    4716            �           2606    16708 "   tbl_edges tbl_edges_target_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_edges
    ADD CONSTRAINT tbl_edges_target_id_fkey FOREIGN KEY (target_id) REFERENCES public.tbl_nodes(id) ON DELETE CASCADE;
 L   ALTER TABLE ONLY public.tbl_edges DROP CONSTRAINT tbl_edges_target_id_fkey;
       public               postgres    false    227    219    4716            �           2606    16713 $   tbl_groups tbl_group_project_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_groups
    ADD CONSTRAINT tbl_group_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.tbl_projects(id) ON DELETE CASCADE;
 N   ALTER TABLE ONLY public.tbl_groups DROP CONSTRAINT tbl_group_project_id_fkey;
       public               postgres    false    223    229    4720            �           2606    16718 )   tbl_groupdata tbl_groupdata_group_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_groupdata
    ADD CONSTRAINT tbl_groupdata_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.tbl_groups(id) ON DELETE CASCADE;
 S   ALTER TABLE ONLY public.tbl_groupdata DROP CONSTRAINT tbl_groupdata_group_id_fkey;
       public               postgres    false    225    4712    223            �           2606    16723 (   tbl_groupdata tbl_groupdata_user_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_groupdata
    ADD CONSTRAINT tbl_groupdata_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.tbl_users(id) ON DELETE CASCADE;
 R   ALTER TABLE ONLY public.tbl_groupdata DROP CONSTRAINT tbl_groupdata_user_id_fkey;
       public               postgres    false    225    4710    221            �           2606    16728 #   tbl_nodes tbl_nodes_project_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_nodes
    ADD CONSTRAINT tbl_nodes_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.tbl_projects(id) ON DELETE CASCADE;
 M   ALTER TABLE ONLY public.tbl_nodes DROP CONSTRAINT tbl_nodes_project_id_fkey;
       public               postgres    false    227    229    4720            �           2606    16733 (   tbl_projects tbl_projects_status_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_projects
    ADD CONSTRAINT tbl_projects_status_id_fkey FOREIGN KEY (status_id) REFERENCES public.tbl_status(id);
 R   ALTER TABLE ONLY public.tbl_projects DROP CONSTRAINT tbl_projects_status_id_fkey;
       public               postgres    false    229    4722    231            �           2606    16738 )   tbl_userdata tbl_userdata_project_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_userdata
    ADD CONSTRAINT tbl_userdata_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.tbl_projects(id) ON DELETE CASCADE;
 S   ALTER TABLE ONLY public.tbl_userdata DROP CONSTRAINT tbl_userdata_project_id_fkey;
       public               postgres    false    237    4720    229            �           2606    16743 &   tbl_userdata tbl_userdata_role_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_userdata
    ADD CONSTRAINT tbl_userdata_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.tbl_roles(id);
 P   ALTER TABLE ONLY public.tbl_userdata DROP CONSTRAINT tbl_userdata_role_id_fkey;
       public               postgres    false    233    4724    237            �           2606    16748 &   tbl_userdata tbl_userdata_user_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tbl_userdata
    ADD CONSTRAINT tbl_userdata_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.tbl_users(id) ON DELETE CASCADE;
 P   ALTER TABLE ONLY public.tbl_userdata DROP CONSTRAINT tbl_userdata_user_id_fkey;
       public               postgres    false    237    221    4710                  x������ � �            x������ � �            x������ � �      "      x������ � �             x������ � �      $      x������ � �      &      x������ � �      *   �   x��;
�@E��#���SX��q@��V"b��g���gu��9���9���v�#�}�<J����'�9i�I#M�hD��nj��=���kn�wh�ȥ oֽsֳe��=�	�֭B�L��YHF1      (   �   x�=�K
�@D�=���G1���"�NŅ�ҝ��@�DM�P}#{Fq�PtU��	W>�ŀ'�F��k8�1r�;1{��ff��b��\�� I��$��YK�O��z�k%*%\B�劏>�&�TE��wN�c 8��t�h�z�~Z{ю�U^��t��� Vux      ,   �   x�u���@DϞb"�^RL�C��e$5�;���q��7Ϟ̸1X��8��=w���Ax�y��՜��EA��Hq��t��K�J�?��ڒS����'UU�#}�����pk4vRՠ�U�Z\/ �$n      .      x������ � �         6  x�eQ�N�0<;_�/�H��g���[A���.H���UH|@(�V��Į��&�%3���ݍ�Q��/�Q�wCk�{l	n��_v.����It�5*{#5����\��I.b�D��Γ��@��Sg*�C{�8XQ�%uqʕ}` C�)�j�g���z>�������IO��#�u瓫<��ƙ�NC�'7��.�Ȑu�T�c}d8x��v�B�5�w�S�Q�L2�%$��Qov
����a7?��;�wV6�A�9�78x�"߽nv��݆�٭V:O�	w{�s���w���Pޫ�u��(��ŏ     