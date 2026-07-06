# Retest Checklist

Run these checks after fixes land:

- [ ] P1 Signup on iOS Safari: Tap Continue after email code
  - Confirm: New account dashboard opens
- [ ] P2 Offline mode on Android Chrome: Open app in airplane mode
  - Confirm: Offline message explains what still works
- [ ] P3 Reminder setup on Android Chrome: Tap time picker with large font enabled
  - Confirm: Picker remains readable and tappable
- [ ] P4 First habit on Android Chrome: Create first habit with emoji and weekday schedule
  - Confirm: Habit appears on Today screen
- [ ] P5 Settings on Desktop Chrome: Open privacy section
  - Confirm: Privacy copy is readable and direct
- [ ] P6 Settings on iOS Safari: Tap Save after changing display name
  - Confirm: Toast confirms settings saved
- [ ] P7 Today screen on iOS Safari: Tap completed habit by accident
  - Confirm: Undo option should be visible
- [ ] P8 First habit on iOS Safari: Type a long habit name
  - Confirm: Name wraps cleanly inside the card

## Coverage Gaps

- [ ] Add coverage for Account deletion
