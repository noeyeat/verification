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
      if (task.done) {
        li.classList.add("done");
      }
      const row = document.createElement("div");
      row.className = "task-row";

      const a = document.createElement("a");
      a.href = `#task-${task.id}`;
      a.textContent = task.title;
      a.setAttribute("aria-label", task.title);
      a.addEventListener("click", (e) => {
        e.preventDefault();
        openDetail(task);
      });

      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "toggle-done";
      const markName = task.done
        ? `Mark incomplete: ${task.title}`
        : `Mark complete: ${task.title}`;
      toggle.setAttribute("aria-label", markName);
      toggle.textContent = task.done ? "Undo" : "Done";
      toggle.addEventListener("click", async (e) => {
        e.preventDefault();
        await setDone(task.id, !task.done);
        await refreshHome();
      });

      row.appendChild(a);
      row.appendChild(toggle);
      const p = document.createElement("p");
      p.className = "meta";
      p.textContent = task.body || "(no body)";
      if (task.done) {
        p.textContent += " · completed";
      }
      li.appendChild(row);
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

  async function setDone(id, done) {
    const res = await fetch(`/api/tasks/${id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ done }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || "update failed");
    }
    return res.json();
  }

  async function refreshHome() {
    const tasks = await fetchTasks();
    const status = document.getElementById("home-status");
    const doneCount = tasks.filter((t) => t.done).length;
    if (!tasks.length) {
      status.textContent = "No tasks yet";
    } else if (doneCount) {
      status.textContent = `${tasks.length} task(s) · ${doneCount} completed`;
    } else {
      status.textContent = `${tasks.length} task(s)`;
    }
    renderList(document.getElementById("task-list"), tasks, "No tasks yet. Create one.");
  }

  function openDetail(task) {
    document.getElementById("detail-heading").textContent = "Task";
    document.getElementById("detail-title").textContent = task.title;
    document.getElementById("detail-body").textContent = task.body || "(no body)";
    const doneLabel = task.done ? "completed" : "incomplete";
    document.getElementById("detail-meta").textContent =
      `id=${task.id} created=${task.created_at || ""} · ${doneLabel}`;
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
    document.getElementById("home-status").textContent = `Saved “${data.task.title}”`;
  });

  document.getElementById("clear-completed").addEventListener("click", async () => {
    const res = await fetch("/api/tasks/clear-completed", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const data = await res.json();
    const status = document.getElementById("home-status");
    if (!res.ok) {
      status.textContent = data.error || "Clear failed";
      return;
    }
    await refreshHome();
    const msg =
      data.removed === 0
        ? "No completed tasks to clear"
        : `Cleared ${data.removed} completed task(s)`;
    status.textContent = msg;
    status.setAttribute("aria-label", msg);
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
