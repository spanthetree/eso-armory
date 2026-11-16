<script>
  let status = $state('checking…');

  $effect(() => {
    fetch('/api/status')
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(() => (status = 'connected'))
      .catch((e) => (status = `unreachable (${e})`));
  });
</script>

<main>
  <h1>ESO Armory</h1>
  <p>New UI scaffold. Backend: {status}</p>
</main>
