import sys
import time
strt = float(time.time())
sys.path.append("..")
from make_hydrodem import hydrodem, agree


print("************ Testing HydroDEM ************")

outdir = r"C:\Users\tbarnhart\projects\datapreptools\data\comparison\01080206_v4\input_data.gdb"
huc8cov = "huc8"
origdem = r"C:\Users\tbarnhart\projects\datapreptools\data\comparison\01080206_v4\Layers\dem"
dendrite = "NHDFlowline"
snap_grid = r"C:\Users\tbarnhart\projects\datapreptools\data\comparison\01080206_v4\Layers\dem"
bowl_polys = "nhd_wbg"
bowl_lines = "wb_srcg"
inwall = "inwall_edit"
drainplug = "sinkpoint_edit"
buffdist = 50
inwallbuffdist = 15 
inwallht = 150000
outwallht = 300000
agreebuf = 60
agreesmooth = -500
agreesharp = -50000
bowldepth = 2000
cellsz = 10
scratchWorkspace = r"C:\Users\tbarnhart\projects\datapreptools\data\comparison\01080206_v4\tmp"
version = None

hydrodem(outdir, huc8cov, origdem, dendrite, snap_grid, bowl_polys, bowl_lines, inwall, drainplug, buffdist, inwallbuffdist, inwallht, outwallht, agreebuf, agreesmooth, agreesharp, bowldepth, cellsz, scratchWorkspace, version = version)

print("Elapsed time: %s minutes"%((time.time() - strt)/60.))