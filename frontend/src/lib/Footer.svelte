<script>
  let { stats = { correct: 0, attempts: 0 } } = $props()
</script>

<footer class="footer">
  {stats.correct} correct out of {stats.attempts} attempted
</footer>

<style>
  .footer {
    text-align: center;
    padding: 14px;
    color: var(--muted);
    border-top: 1px solid var(--border);
    font-size: 14px;
  }
</style>
