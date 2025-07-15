const pendingTasks = JSON.parse(document.getElementById("pending-data").textContent);

pendingTasks.forEach(task => {
  const countdownElem = document.getElementById("countdown-" + task.id);

  const interval = setInterval(() => {
    const now = new Date();
    const diff = new Date(task.deadline) - now;

    if (diff <= 0) {
      clearInterval(interval);
      countdownElem.innerText = "Expired";
      fetch("/fail/" + task.id)
        .then(() => {
          const taskItem = document.getElementById("task-" + task.id);
          taskItem.style.opacity = 0.5;
          taskItem.innerHTML += "<br><span style='color:red;'>❌ Task failed automatically</span>";
        });
    } else {
      const d = Math.floor(diff / (1000 * 60 * 60 * 24));
      const h = Math.floor((diff / (1000 * 60 * 60)) % 24);
      const m = Math.floor((diff / (1000 * 60)) % 60);
      const s = Math.floor((diff / 1000) % 60);
      countdownElem.innerText = `${d}d ${h}h ${m}m ${s}s`;
    }
  }, 1000);
});
function markComplete(taskId) {
  fetch("/complete/" + taskId)
    .then(() => {
      const taskElem = document.getElementById("task-" + taskId);
      taskElem.style.opacity = 0.5;
      taskElem.innerHTML += "<br><span style='color:green;'>✅ Task marked as completed</span>";
    });
}