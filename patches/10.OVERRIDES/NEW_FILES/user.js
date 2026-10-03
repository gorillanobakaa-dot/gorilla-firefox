// Gorilla Unleashed — Wayland runtime overrides
// Keeps GPU process off on Wayland: the compositor widget in the GPU process
// has no wl_egl_window (GtkCompositorWidgetInitData carries no Wayland handle),
// so EGL surface creation fails and the window stays black.
// VA-API decode still works via the RDD process (media.rdd-ffmpeg.enabled).
user_pref("layers.gpu-process.enabled", false);
user_pref("layers.gpu-process.force-enabled", false);
user_pref("media.gpu-process-decoder", false);

// gfx.x11-egl.force-enabled has no effect in a cairo-gtk3-wayland build
// (the #ifdef MOZ_X11 guard skips the entire InitX11EGLConfig body), but
// remove it to keep prefs clean and avoid confusion.
user_pref("gfx.x11-egl.force-enabled", false);

// ── VA-API hardware video decode (H.264 via i965 in RDD process) ──────────
// The Gorilla hardware-only policy (PDMFactory.cpp) rejects ALL video unless
// the decoder reports DecodeSupport::HardwareDecode. These prefs ensure VA-API
// is initialised in the RDD process and that H.264 never silently falls back
// to software decode (which the C++ policy would reject anyway).
// LIBVA_DRIVER_NAME=i965 must be set in /etc/environment (it is).
user_pref("media.ffmpeg.vaapi.enabled", true);
user_pref("media.ffmpeg.vaapi.decode.force-enabled", true);

// ── VA-API surface zero-copy: bypass gfxInfo blocklist ────────────────────
// media.ffmpeg.vaapi.force-surface-zero-copy defaults to 2 (gfxInfo-controlled).
// State 1 skips the gfxInfo GetFeatureStatus call entirely, so FEATURE_ALLOW_ALWAYS
// vs FEATURE_STATUS_OK ambiguity cannot block zero-copy. Without this, gfxInfo
// returning anything other than FEATURE_ALLOW_ALWAYS sets mEnvironment=Blocklisted,
// and the Gorilla UserEnable() at gfxPlatformGtk.cpp:282 is overridden (UserEnable
// ranks below Environment). Belt-and-suspenders with the C++ UserForceEnable fix.
user_pref("media.ffmpeg.vaapi.force-surface-zero-copy", 1);

// ── WebRender native Wayland compositor (hardware overlay, low memory BW) ─
// gfx.webrender.compositor defaults to false on Linux, so CompositorType()
// returns DRAW instead of WAYLAND. Without native compositor, VA-API decoded
// NV12 DMABuf frames go through WebRender's full GL pipeline (YUV→RGB shader
// → RGBA framebuffer → Mutter reads), burning ~4× extra GPU memory bandwidth
// on UMA (Ivy Bridge). force-enabled bypasses the gfxInfo blocklist and
// activates the Wayland native compositor so VA-API NV12 surfaces are
// submitted directly as KMS hardware plane overlays, cutting IMC bandwidth
// from ~2500 MiB/s to ~500 MiB/s.
// Side-effect: UploadSWDecodeToDMABuf() also becomes true (GetWebRenderCompositorType()
// == WAYLAND) so if SW decode ever runs it also takes the zero-copy DMABuf path.
user_pref("gfx.webrender.compositor.force-enabled", true);

// ── Codec policy: H.264-only ──────────────────────────────────────────────
// Belt-and-suspenders with the compiled-in Gorilla DecoderTraits patch that
// returns CANPLAY_NO for VP9/AV1/WebM. Setting these prefs also makes
// YouTube's isTypeSupported() calls return false at the JS level so YouTube
// negotiates H.264 MP4 without attempting any VP9/AV1 MSE SourceBuffer.
user_pref("media.av1.enabled", false);
user_pref("media.vp9.enabled", false);
user_pref("media.mediasource.vp9.enabled", false);
