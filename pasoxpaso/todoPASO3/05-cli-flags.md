# Step 05: CLI Flags

**Goal:** Add command-line flags to `cliper.py` for user control of face tracking

---

## 📋 CLI Design

Users should be able to enable/configure face tracking via interactive prompts:

```
Enable face tracking for dynamic reframing? (y/n): y
Face tracking style:
  1. keep_in_frame (recommended) - Minimal movement
  2. centered - Always center on face
Choice: 1
```

---

## ✅ Tasks

### Task 5.1: Find the Video Export Section

**File:** `/cliper.py`

**Exact location:** Function `opcion_exportar_clips()` around **line 1068**

You'll find this code:
```python
# Line 1062-1068
aspect_map = {
    "1": None,      # Original
    "2": "9:16",    # Vertical
    "3": "1:1"      # Square
}

aspect_ratio = aspect_map[aspect_choice]  # ← Line 1068
```

And later at **line 1162-1178**:
```python
# Line 1162
exporter = VideoExporter(output_dir="output")

# Line 1168
exported_paths = exporter.export_clips(...)
```

- [ ] Located line 1068 (after `aspect_ratio` assignment)
- [ ] Located line 1162-1168 (VideoExporter instantiation and call)

---

### Task 5.2: Add Face Tracking Prompt

**Insert this code at line ~1069** (immediately after `aspect_ratio = aspect_map[aspect_choice]`):

```python
# Face tracking configuration (ADD AFTER LINE 1068)
enable_face_tracking = False
face_tracking_style = "keep_in_frame"
face_tracking_sample_rate = 3

if aspect_ratio == "9:16":  # Only relevant for vertical videos
    enable_face_tracking = Confirm.ask(
        "\n[cyan]Enable face tracking for dynamic reframing?[/cyan]",
        default=False
    )

    if enable_face_tracking:
        console.print("\n[cyan]Face Tracking Style:[/cyan]")
        console.print("  1. keep_in_frame (recommended) - Minimal movement, professional look")
        console.print("  2. centered - Always center on face (can be jittery)")

        style_choice = Prompt.ask(
            "Choice",
            choices=["1", "2"],
            default="1"
        )

        face_tracking_style = "keep_in_frame" if style_choice == "1" else "centered"

        # Advanced: frame sampling (optional, can skip for now)
        advanced = Confirm.ask(
            "\n[dim]Configure advanced settings?[/dim]",
            default=False
        )

        if advanced:
            sample_rate_input = Prompt.ask(
                "Frame sample rate (process every N frames)",
                default="3"
            )
            try:
                face_tracking_sample_rate = int(sample_rate_input)
            except ValueError:
                console.print("[yellow]Invalid input, using default: 3[/yellow]")
                face_tracking_sample_rate = 3
```

- [ ] Added face tracking enable prompt
- [ ] Added style selection (keep_in_frame vs centered)
- [ ] Added optional advanced settings prompt
- [ ] Only shows prompts when aspect_ratio is "9:16"

---

### Task 5.3: Pass Parameters to `export_clips()`

**Update the `export_clips()` call at line ~1168:**

**Before:**
```python
exported_paths = exporter.export_clips(
    video_path=video_path,
    clips=clips_to_export,
    aspect_ratio=aspect_ratio,
    video_name=video_id,
    add_subtitles=add_subtitles,
    transcript_path=transcript_path,
    subtitle_style=subtitle_style,
    organize_by_style=organize_by_style,
    clip_styles=clip_styles_map
)
```

**After:**
```python
exported_paths = exporter.export_clips(
    video_path=video_path,
    clips=clips_to_export,
    aspect_ratio=aspect_ratio,
    video_name=video_id,
    add_subtitles=add_subtitles,
    transcript_path=transcript_path,
    subtitle_style=subtitle_style,
    organize_by_style=organize_by_style,
    clip_styles=clip_styles_map,
    # NEW: Face tracking
    enable_face_tracking=enable_face_tracking,
    face_tracking_style=face_tracking_style,
    face_tracking_sample_rate=face_tracking_sample_rate
)
```

- [ ] Added face tracking parameters to `export_clips()` call

---

### Task 5.4: Add Visual Feedback

**After the user makes their selection, show confirmation:**

```python
if enable_face_tracking:
    console.print("\n[green]✓[/green] Face tracking enabled:")
    console.print(f"  Strategy: [cyan]{face_tracking_style}[/cyan]")
    console.print(f"  Sample rate: every [cyan]{face_tracking_sample_rate}[/cyan] frame(s)")
    console.print()
```

- [ ] Added visual confirmation of face tracking settings

---

### Task 5.5: Add Info Message During Export

**The existing progress bar in `video_exporter.py` will show export progress.**

**Optionally, you can add a message before export starts:**

```python
if enable_face_tracking:
    console.print("[cyan]Starting export with face tracking...[/cyan]")
    console.print("[dim]This may take longer than static crop due to AI processing[/dim]\n")
else:
    console.print("[cyan]Starting export...[/cyan]\n")
```

- [ ] Added informative message about face tracking processing

---

## 🎯 Validation Checklist

Before moving to Step 06:

- [ ] Face tracking prompt appears when selecting 9:16 aspect ratio
- [ ] User can choose between "keep_in_frame" and "centered"
- [ ] Advanced settings (frame rate) are optional
- [ ] Parameters are passed correctly to `export_clips()`
- [ ] Visual feedback shows selected settings
- [ ] No syntax errors in `cliper.py`

---

## 📝 User Experience Flow

```
User selects "Export clips"
  ↓
Aspect ratio: 9:16?
  ↓
Enable face tracking? [y/n]
  ├─ n → Static crop (original behavior)
  └─ y → Face tracking style?
         ├─ 1: keep_in_frame (recommended)
         └─ 2: centered
            ↓
         Advanced settings? [y/n]
            ├─ n → Use defaults
            └─ y → Frame sample rate? [3]
               ↓
            Start export with AI reframing
```

---

## 💡 Future Enhancement Ideas

**(Not for this step, just notes for later):**

1. **Presets:** "Interview mode", "Energetic mode", "Cinematic mode"
2. **Auto-detect:** Analyze video first, recommend settings
3. **Config file:** Save user preferences
4. **Batch mode:** Apply same settings to all clips
5. **Preview:** Show first 5 seconds of reframed video before full export

---

## ❓ Troubleshooting

**Problem:** Prompt doesn't appear
**Solution:** Check that `aspect_ratio == "9:16"` condition is met

**Problem:** Wrong parameters passed to export_clips()
**Solution:** Verify variable names match exactly. Use `exporter` not `video_exporter`

**Problem:** User confused by options
**Solution:** Add more descriptive help text explaining each strategy

---

**Next Step:** `06-testing.md` →
