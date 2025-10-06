import sys
import subprocess
import threading
import os
import streamlit.components.v1 as components

# Install streamlit jika belum ada
try:
    import streamlit as st
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
    import streamlit as st


def run_ffmpeg(video_path, stream_key, is_shorts, log_callback):
    # ✅ Server YouTube Live
    output_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    scale = "-vf scale=720:1280" if is_shorts else ""

    cmd = [
        "ffmpeg", "-re", "-i", video_path,
        "-c:v", "libx264", "-preset", "veryfast", "-b:v", "2500k",
        "-maxrate", "2500k", "-bufsize", "5000k",
        "-g", "60", "-keyint_min", "60",
        "-c:a", "aac", "-b:a", "128k",
        "-f", "flv"
    ]
    if scale:
        cmd += scale.split()
    cmd.append(output_url)

    log_callback(f"Menjalankan: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            log_callback(line.strip())
        process.wait()
    except Exception as e:
        log_callback(f"Error: {e}")
    finally:
        log_callback("Streaming selesai atau dihentikan.")


def main():
    # ✅ Page config harus pertama
    st.set_page_config(
        page_title="Streaming YouTube Live",
        page_icon="🎥",
        layout="wide"
    )

    # ✅ Naikkan limit upload file ke 10 GB → cukup untuk video 2 jam
    st.config.set_option("server.maxUploadSize", 10000)

    st.title("Live Streaming ke YouTube")

    # ✅ Bagian iklan opsional
    show_ads = st.checkbox("Tampilkan Iklan", value=True)
    if show_ads:
        st.subheader("Iklan Sponsor")
        components.html(
            """
            <div style="background:#f0f2f6;padding:20px;border-radius:10px;text-align:center">
                <script type='text/javascript' 
                        src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'>
                </script>
                <p style="color:#888">Iklan akan muncul di sini</p>
            </div>
            """,
            height=300
        )

    # ✅ Daftar file video lokal
    video_files = [f for f in os.listdir('.') if f.endswith(('.mp4', '.flv'))]

    st.write("Video yang tersedia:")
    selected_video = st.selectbox("Pilih video", video_files) if video_files else None

    # ✅ Upload file video panjang (mp4/flv) – aman hingga 10 GB
    uploaded_file = st.file_uploader(
        "Atau upload video panjang (mp4/flv - codec H264/AAC)",
        type=['mp4', 'flv']
    )

    if uploaded_file:
        os.makedirs("uploads", exist_ok=True)
        video_path = os.path.join("uploads", uploaded_file.name)
        with open(video_path, "wb") as f:
            # Simpan per chunk 1MB → aman untuk file besar
            for chunk in iter(lambda: uploaded_file.read(1024 * 1024), b""):
                f.write(chunk)
        st.success(f"✅ Video berhasil diupload! ({video_path})")
    elif selected_video:
        video_path = selected_video
    else:
        video_path = None

    # ✅ Input stream key
    stream_key = st.text_input("YouTube Stream Key", type="password")
    is_shorts = st.checkbox("Mode Shorts (720x1280)")

    log_placeholder = st.empty()
    logs = []
    streaming = st.session_state.get('streaming', False)

    def log_callback(msg):
        # Perbaikan pesan error agar lebih ramah
        if "status code 400" in msg:
            logs.append("❌ Permintaan ditolak server (400 - Bad Request). Periksa stream key atau format video.")
        else:
            logs.append(msg)
        try:
            log_placeholder.text("\n".join(logs[-20:]))
        except:
            print(msg)

    if 'ffmpeg_thread' not in st.session_state:
        st.session_state['ffmpeg_thread'] = None

    # ✅ Tombol Jalankan Streaming
    if st.button("Jalankan Streaming"):
        if not video_path or not stream_key:
            st.error("Video dan stream key harus diisi!")
        else:
            st.session_state['streaming'] = True
            st.session_state['ffmpeg_thread'] = threading.Thread(
                target=run_ffmpeg, args=(video_path, stream_key, is_shorts, log_callback), daemon=True)
            st.session_state['ffmpeg_thread'].start()
            st.success("🎬 Streaming dimulai ke YouTube!")

    # ✅ Tombol Stop Streaming
    if st.button("Stop Streaming"):
        st.session_state['streaming'] = False
        os.system("pkill ffmpeg")
        if os.path.exists("temp_video.mp4"):
            os.remove("temp_video.mp4")
        st.warning("⏹️ Streaming dihentikan!")

    log_placeholder.text("\n".join(logs[-20:]))


if __name__ == '__main__':
    main()
