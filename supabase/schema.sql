-- Digital Lab Office — база задач
-- Вставить целиком в Supabase → SQL Editor → Run

create table if not exists projects (
  id          bigint generated always as identity primary key,
  title       text not null,
  client      text,
  kind        text,                       -- лендинг, сайт, бот, mini app, автоматизация, дизайн, маркетинг, внутреннее
  status      text not null default 'новый',  -- новый, в работе, на согласовании, готов, пауза
  deadline    date,
  budget      numeric,
  brief       text,                       -- ТЗ / описание
  links       text,                       -- превью, репозиторий, макеты
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create table if not exists tasks (
  id          bigint generated always as identity primary key,
  project_id  bigint references projects(id) on delete set null,
  title       text not null,
  details     text,
  assignee    text not null default 'alina',  -- alina, alice, dmitry, maria, maxim, ilya, alexander, daria
  area        text not null default 'работа', -- работа | личное
  status      text not null default 'todo',   -- todo, doing, review, done
  priority    smallint not null default 2,    -- 1 высокий, 2 обычный, 3 низкий
  due         timestamptz,
  remind_at   timestamptz,
  reminded    boolean not null default false,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  done_at     timestamptz
);

create table if not exists notes (
  id          bigint generated always as identity primary key,
  author      text not null,
  text        text not null,
  created_at  timestamptz not null default now()
);

create index if not exists tasks_status_idx   on tasks(status);
create index if not exists tasks_project_idx  on tasks(project_id);
create index if not exists tasks_remind_idx   on tasks(remind_at) where reminded = false;

-- Прогресс по проектам (для дашборда)
create or replace view project_progress with (security_invoker = true) as
select p.*,
       count(t.id)                                   as tasks_total,
       count(t.id) filter (where t.status = 'done')  as tasks_done,
       case when count(t.id) = 0 then 0
            else round(100.0 * count(t.id) filter (where t.status = 'done') / count(t.id))
       end                                           as percent
from projects p
left join tasks t on t.project_id = p.id
group by p.id;

-- Закрываем таблицы от публичного доступа: читать/писать может только сервер с service-ключом
alter table projects enable row level security;
alter table tasks    enable row level security;
alter table notes    enable row level security;
