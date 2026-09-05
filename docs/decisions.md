## Decisions

- Preserve the existing FastAPI and SQLAlchemy architecture.
- Keep booking transitions in a service so capacity and waitlist changes remain
  transactional.
- Treat membership alert dismissal as tied to one expiry date; changing the
  expiry date naturally makes the alert eligible again.
- Use a small dependency-free frontend so the assignment remains runnable
  without a package-install step.