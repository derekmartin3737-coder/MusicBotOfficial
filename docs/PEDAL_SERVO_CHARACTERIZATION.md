# Pedal Servo Characterization

Use this bench workflow to measure the real timing of the microservo that will drive the sustain pedal.

## Files

- Bench sketch: [PedalServoBenchTest.ino](../arduino/PedalServoBenchTest/PedalServoBenchTest.ino)
- Reaction-time runner: [pedal_servo_reaction_test.py](../scripts/pedal_servo_reaction_test.py)
- Video-analysis log template: [pedal_servo_test_log_template.csv](pedal_servo_test_log_template.csv)
- Reaction-test outputs are generated locally as `docs\pedal_servo_reaction_results.csv` and `docs\pedal_servo_reaction_summary.json`.

## Goal

We want numbers that let us convert MIDI sustain-pedal events into accurate servo timing:

- command-to-first-motion delay
- command-to-pedal-contact delay
- command-to-full-down delay
- command-to-release-start delay
- command-to-pedal-clear delay
- command-to-full-up delay
- whether the servo chatters, stalls, or overshoots under real load

## Reaction-Time Test Setup

1. Connect the servo signal wire to Arduino digital pin `2`.
2. Power the servo from an external `5V` supply if possible.
3. Share ground between the Arduino and the servo supply.
4. Mount the servo to the actual pedal linkage, or as close to the final load as possible.
5. Upload [PedalServoBenchTest.ino](../arduino/PedalServoBenchTest/PedalServoBenchTest.ino).
6. Close Arduino IDE so it does not hold the COM port open.
7. Run:

   ```powershell
   python scripts\pedal_servo_reaction_test.py --port COM7
   ```

8. Press `Enter` once to begin the test.
9. The first move is a priming move and is not recorded.
10. After that, the servo alternates directions automatically.
11. Press `Space` each time it reaches the next endpoint.
12. The default test records `10` total moves with a `1.5 second` pause between moves.

The runner saves the raw reaction times and the average estimated tip speed automatically.

## What The Reaction Test Measures

It estimates:

- average command-to-down-position travel time
- average command-to-up-position travel time
- overall average travel time across the measured moves
- average estimated tip speed of the servo arm

This is useful for rough pedal lead timing, but it still includes human reaction delay.

## Why Keep The Video Method

The reaction-time test is faster, but the original slow-motion video workflow is still better when you want:

- more accurate true travel timing
- first-motion delay
- pedal-contact timing
- stall or chatter diagnosis

Use the video workflow if you need more accuracy than a human spacebar press can provide.

## Video Test Setup

1. Connect the servo signal wire to Arduino digital pin `2`.
2. Power the servo from an external `5V` supply if possible.
3. Share ground between the Arduino and the servo supply.
4. Mount the servo to the actual pedal linkage, or as close to the final load as possible.
5. Upload [PedalServoBenchTest.ino](../arduino/PedalServoBenchTest/PedalServoBenchTest.ino).
6. Film the built-in Arduino LED and the servo or pedal linkage in the same shot.
7. Record at `120 FPS` or `240 FPS` if your phone supports it.

The sketch flashes the built-in LED exactly when the command is issued. That LED flash is your frame-zero timing reference.

## What To Measure Per Trial

For each `pedal_down` command:

- `first_motion_ms`: time from LED flash to the first visible servo movement
- `pedal_contact_ms`: time from LED flash to the moment the pedal linkage first contacts and begins moving the pedal
- `full_down_ms`: time from LED flash to full pedal-down position

For each `pedal_up` command:

- `first_motion_ms`: time from LED flash to the first visible return movement
- `pedal_clear_ms`: time from LED flash until the pedal is clearly no longer depressed
- `full_up_ms`: time from LED flash to full return

Also record:

- `supply_voltage_v`
- `video_fps`
- `up_angle_deg`
- `down_angle_deg`
- load description
- audible noise rating
- chatter, stall, or missed-motion notes

## How To Convert Video Frames To Milliseconds

Use:

- `milliseconds = (frame_count / video_fps) * 1000`

Examples:

- `3 frames at 120 FPS = 25.0 ms`
- `6 frames at 240 FPS = 25.0 ms`

## Recommended Derived Values

After you log several successful trials at the real load:

- `pedal_down_lead_ms = median(pedal_contact_ms) + 10 to 20 ms`
- `pedal_up_lead_ms = median(pedal_clear_ms) + 10 to 20 ms`
- `pedal_down_settle_ms = median(full_down_ms)`
- `pedal_up_settle_ms = median(full_up_ms)`

These are the values we will use later when we map MIDI `CC64` sustain data into servo commands.

From the reaction-time runner, the most useful quick estimates are:

- overall average travel time
- average `down` travel time
- average `up` travel time
- average tip speed in inches per second for the `0.5 inch` arm

## Notes On Angles

Pick the smallest reliable movement that still gives:

- a clear full pedal-down
- a clear full pedal release
- no binding
- no constant buzzing at the end stop

If the servo can only reach the position by stalling or buzzing hard, the angle or linkage needs to change.

The current reaction-time sketch defaults to a full-range test:

- `up = 0 degrees`
- `down = 180 degrees`

Reduce those limits if the servo or linkage binds.

## Signs The Servo Is Too Weak

- delayed or inconsistent motion under pedal load
- obvious stalling or buzzing at the bottom
- failure to return quickly
- large variation between trials

If that happens, the timing numbers will not be stable enough for musical pedal control and a stronger servo is likely needed.
