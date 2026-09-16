(() => {
  const views = {
    home: document.getElementById("view-home"),
    create: document.getElementById("view-create"),
    search: document.getElementById("view-search"),
    detail: document.getElementById("view-detail"),
  };
  const nav = {
    home: document.getElementById("nav-home"),
    new: document.getElementById("nav-new"),
    search: document.getElementById("nav-search"),
  };

  function show(name) {
    Object.entries(views).forEach(([key, el]) => {
      el.hidden = key !== name;
    });
    nav.home.setAttribute("aria-current", name === "home" ? "page" : "false");
    nav.new.setAttribute("aria-current", name === "create" ? "page" : "false");
    nav.search.setAttribute("aria-current", name === "search" ? "page" : "false");
  }

  function renderList(el, tasks, emptyMsg) {
    el.innerHTML = "";
    if (!tasks.length) {
      const li = document.createElement("li");
      li.textContent = emptyMsg;
      el.appendChild(li);
      return;
    }
    for (const task of tasks) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = `#task-${task.id}`;
      a.textContent = task.title;
      a.setAttribute("aria-label", task.title);
      a.addEventListener("click", (e) => {
        e.preventDefault();
        openDetail(task);
      });
      const p = document.createElement("p");
      p.className = "meta";
      p.textContent = task.body || "(no body)";
      li.appendChild(a);
      li.appendChild(p);
      el.appendChild(li);
    }
  }

  async function fetchTasks(q) {
    const url = q ? `/api/tasks?q=${encodeURIComponent(q)}` : "/api/tasks";
    const res = await fetch(url);
    const data = await res.json();
    return data.tasks || [];
  }

  async function refreshHome() {
    const tasks = await fetchTasks();
    const status = document.getElementById("home-status");
    status.textContent = tasks.length ? `${tasks.length} task(s)` : "No tasks yet";
    renderList(document.getElementById("task-list"), tasks, "No tasks yet. Create one.");
  }

  function openDetail(task) {
    document.getElementById("detail-heading").textContent = "Task";
    document.getElementById("detail-title").textContent = task.title;
    document.getElementById("detail-body").textContent = task.body || "(no body)";
    document.getElementById("detail-meta").textContent = `id=${task.id} created=${task.created_at || ""}`;
    show("detail");
  }

  nav.home.addEventListener("click", async () => {
    show("home");
    await refreshHome();
  });
  nav.new.addEventListener("click", () => {
    document.getElementById("create-form").reset();
    document.getElementById("create-status").textContent = "";
    show("create");
    document.getElementById("task-title").focus();
  });
  nav.search.addEventListener("click", () => {
    document.getElementById("search-input").value = "";
    document.getElementById("search-status").textContent = "";
    document.getElementById("search-results").innerHTML = "";
    show("search");
    document.getElementById("search-input").focus();
  });

  document.getElementById("cancel-create").addEventListener("click", async () => {
    show("home");
    await refreshHome();
  });

  document.getElementById("create-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("task-title").value.trim();
    const body = document.getElementById("task-body").value.trim();
    const res = await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, body }),
    });
    const data = await res.json();
    const status = document.getElementById("create-status");
    if (!res.ok) {
      status.textContent = data.error || "Save failed";
      return;
    }
    status.textContent = "Task saved";
    status.setAttribute("aria-label", "Task saved");
    show("home");
    await refreshHome();
    // flash saved title presence
    document.getElementById("home-status").textContent = `Saved “${data.task.title}”`;
  });

  let searchTimer = null;
  document.getElementById("search-input").addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(runSearch, 150);
  });

  async function runSearch() {
    const q = document.getElementById("search-input").value.trim();
    const status = document.getElementById("search-status");
    const results = document.getElementById("search-results");
    if (!q) {
      status.textContent = "";
      results.innerHTML = "";
      return;
    }
    const tasks = await fetchTasks(q);
    if (!tasks.length) {
      status.textContent = "No matching tasks";
      status.setAttribute("aria-label", "No matching tasks");
      results.innerHTML = "";
      return;
    }
    status.textContent = `${tasks.length} match(es) for “${q}”`;
    renderList(results, tasks, "");
  }

  document.getElementById("clear-search").addEventListener("click", () => {
    document.getElementById("search-input").value = "";
    document.getElementById("search-status").textContent = "";
    document.getElementById("search-results").innerHTML = "";
    document.getElementById("search-input").focus();
  });

  document.getElementById("back-home").addEventListener("click", async () => {
    show("home");
    await refreshHome();
  });

  fetch("/api/health")
    .then((r) => r.json())
    .then((h) => {
      document.getElementById("build-label").textContent =
        `TaskBoard build=${h.build} · data=${h.data_dir}`;
    })
    .catch(() => {});

  refreshHome();
})();
