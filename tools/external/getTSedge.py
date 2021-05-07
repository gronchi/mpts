import numpy as np
import matplotlib.pyplot as plt
import itertools
import sys
sys.path.append('/afs/ipp/aug/ads-diags/common/python/lib')
import dd
import map_equ
from scipy.interpolate import interp1d

eqm = map_equ.equ_map()
marker = itertools.cycle(('o', 's', 'd', 'v', '^', '<', '>', '*', '.'))


shot_list = np.array([37472])
trigger_t = np.array([6])

for i in range(len(shot_list)):
    shotnumber = shot_list[i]
    # get flux coordinates
    status = eqm.Open(shotnumber, diag='EQH')
    R = np.arange(2.0, 2.16, 0.005)
    Z = 0.155 * np.ones(R.size)
    rho = eqm.rz2rho(R, Z, t_in=trigger_t[i], coord_out='rho_pol')[0]
    rho2R = interp1d(rho, R, kind='cubic')
    ida = dd.shotfile('IDA', shotnumber)
    Te_ida = ida('Te')
    ne_ida = ida('ne')
    ida.close()
    index_ida = np.argmin(np.abs(Te_ida.time - trigger_t[i]))
    rho_valid_index = np.logical_and(Te_ida.area[index_ida] > rho.min(), Te_ida.area[index_ida] < rho.max())

    # get Thomson scattering data from edge
    vta = dd.shotfile('VTA', shotnumber)
    Te_e = vta('Te_e').data
    SigTe_e = vta('SigTe_e').data
    SigNe_e = vta('SigNe_e').data
    Ne_e = vta('Ne_e').data
    R_edge = vta('R_edge').data
    Z_edge = vta('Z_edge').data
    t = vta('Te_e').time
    vta.close()
    index_vta = np.argmin(np.abs(t - trigger_t[i]))
    m_ = next(marker)

    fig, ((ax1, ax2)) = plt.subplots(1, 2, figsize=(1.4 * 4.5 * 2, 1.4 * 3))
    ax1.errorbar(R_edge[index_vta:index_vta + 6], Te_e[index_vta:index_vta + 6, 4], yerr=SigTe_e[index_vta:index_vta + 6, 4],
                 linestyle="None", label="#%d@2.5s" % shotnumber, marker=m_)
    ax1.plot(rho2R(Te_ida.area[index_ida, rho_valid_index]), Te_ida.data[index_ida, rho_valid_index])
    ax1.set_xlabel("R [m]")
    ax1.set_ylabel("Te [eV]")
    ax1.set_title("Z=%.3f m" % Z_edge[4])
    ax1.vlines([2.135 - 0.007, 2.135 + 0.008], 0, 1, transform=ax1.get_xaxis_transform(), colors='r', linestyles="dashed")
    ax1.set_xlim(2.110, 2.15)
    ax1.legend()
    ax1.grid(True)

    ax2.errorbar(R_edge[index_vta:index_vta + 6], Ne_e[index_vta:index_vta + 6, 4], yerr=SigNe_e[index_vta:index_vta + 6, 4],
                 linestyle="None", label="#%d@2.5s" % shotnumber, marker=m_)
    ax2.plot(rho2R(ne_ida.area[index_ida, rho_valid_index]), ne_ida.data[index_ida, rho_valid_index])
    ax2.set_xlabel("R [m]")
    ax2.set_ylabel(r"Ne [$m^{-3}$]")
    ax2.set_title("Z=%.3f m" % Z_edge[4])
    ax2.vlines([2.135 - 0.007, 2.135 + 0.008], 0, 1, transform=ax2.get_xaxis_transform(), colors='r', linestyles="dashed")
    ax2.legend()
    ax2.set_xlim(2.110, 2.15)
    ax2.grid(True)

    plt.tight_layout()
    fig.savefig("%d_Te_ne_edge.png" % shotnumber)
    plt.show()
