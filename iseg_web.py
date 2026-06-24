# ===== RS232c =====
import serial
import time

class NHQ:
    def __init__(self, port):
        self.ser = serial.Serial(port, 9600, timeout=0.5)
        self.sync()

    def sync(self):
        self.ser.write(b'\r\n')
        time.sleep(0.1)
        self.ser.reset_input_buffer()

    def send(self, cmd):
        for ch in cmd + '\r\n':
            self.ser.write(ch.encode())
            time.sleep(0.003)

        echo = self.ser.readline().decode(errors='ignore').strip()
        resp = self.ser.readline().decode(errors='ignore').strip()
        return resp


# ======== Streamlit UI ========
import streamlit as st

st.set_page_config(page_title="iSeg HV control")
st.title("iSeg NHQ HV control")


def init_hv(port):
    try:
        return NHQ(port)
    except serial.SerialException:
        return None


hv1 = init_hv('/dev/ttyUSB0')
hv2 = init_hv('/dev/ttyUSB1')

if hv1 is None:
    st.info("USB0が接続されていません")
if hv2 is None:
    st.info("USB1が接続されていません")
if hv1 is None or hv2 is None:
    st.stop()

# print(hv1.send("#"))
# print(hv2.send("U1"))

def apply_all():
    for title, hv, ch in PANELS:
        hv.send(f"G{ch}")
    time.sleep(3)
    
def shutdown_all():
    for title, hv, ch in PANELS:
        key = f"set_hv_{hv}_{ch}"
        st.session_state[key] = 0
        hv.send(f"D{ch}=0")
        hv.send(f"G{ch}")
    
def update_set_voltage(hv, ch, key):
    value = st.session_state[key]
    hv.send(f"D{ch}={value}")

def hv_panel(title, hv, ch):
    key = f"set_hv_{hv}_{ch}"
    if key not in st.session_state:
        st.session_state[key] = int(hv.send(f"D{ch}"))
        
    st.subheader(title)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.number_input(
            f"Set {title} [V]",
            value=int(st.session_state[key]),
            key=key,
            on_change=update_set_voltage,
            args=(hv, ch, key),
            step=1
        )
    with col2:
        st.metric(
            f"Measured Set {title} [V]",
            st.session_state[key]
       )
    with col3:
        st.metric(
            f"Measured {title} [V]",
            hv.send(f"U{ch}")
        )
    with col4:
        st.metric(
            f"Measured Current {title} [A]",
            hv.send(f"I{ch}")
        )

PANELS = [
    ("HV1", hv1, 1),
    ("HV2", hv1, 2),
    ("HV3", hv2, 1),
    ("HV4", hv2, 2),
]

for title, hv, ch in PANELS:
    hv_panel(title, hv, ch)
    
col0, col1, col2, spacer = st.columns([1,1,1,3])
with col0:
    st.button("Update", use_container_width=True, on_click=lambda: None)
with col1:
    st.button("Apply", on_click=apply_all, use_container_width=True)
with col2:
    st.button("Shutdown all", on_click=shutdown_all, use_container_width=True)
# st.button("Apply", on_click=apply_all)
# st.button("Shutdown all", on_click=shutdown_all)


# ======== Ramp speed control ========
def update_ramp_speed(hv, ch, key):
    value = int(st.session_state[key])
    print(f"Set ramp speed ch{ch}: {value}")
    hv.send(f"V{ch}={value}")
    
with st.expander("Ramp speed control"):
    for title, hv, ch in PANELS:
        key = f"ramp_speed_{hv}_{ch}"
        if key not in st.session_state:
            st.session_state[key] = int(hv.send(f"V{ch}"))
        
        st.number_input(
            f"Ramp speed {title} [V/s]",
            value=int(st.session_state[key]),
            key=key,
            on_change=update_ramp_speed,
            args=(hv, ch, key),
            step=10
        )