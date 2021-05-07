import dd_20180130
import map_equ_20180130
import dd
import numpy as np

sf = dd_20180130.shotfile()
eqm = map_equ_20180130.equ_map()

nshot = 35759
eq_diag = 'EQH'

status = eqm.Open(nshot, diag=eq_diag)
# rho = eqm.rz2rho([2.135 - 0.007, 2.135 + 0.008, 2.135 - 0.02, 0.135 + 0.02], [0.155, 0.155, 0.155, 0.155], t_in=4.004, coord_out='rho_pol')
rho = eqm.rz2rho([2.135 - 0.007, 2.135 + 0.008], [0.155, 0.155], t_in=4.004, coord_out='rho_pol')[0]

print(rho)


ida = dd.shotfile('IDA', nshot)
Te = ida('Te')
ne = ida('ne')
ida.close()
i = np.argmin(np.abs(Te.time - 4.004))
j1 = np.argmin(np.abs(Te.area[i] - rho[0, 0]))
j2 = np.argmin(np.abs(Te.area[i] - rho[0, 1]))
print(Te.data[i, j2], ne.data[i, j2], Te.data[i, j1], ne.data[i, j1], rho[0, 0], rho[0, 1])

##%%

ida = dd.shotfile('IDA', nshot)


shots= [35741, 35742, 35743, 35745, 35746, 35747, 35748, 35749, 35750, 35751, 35752, 35753, 35754, 35756, 35757, 35758, 35759, 35761, 35763, 35764, 35766, 35767, 35768, 35769, 35770, 35771, 35772, 35773, 35774, 35775, 35776, 35778, 35780]
for shot in shots:
    tree = mds.Tree("mpts", shot_number)
    delay = tree.getNode("\\adc").data()/1e6
    scope = tree.getNode("\\scope")
    status = eqm.Open(nshot, diag=eq_diag)
    # rho = eqm.rz2rho([2.135 - 0.007, 2.135 + 0.008, 2.135 - 0.02, 0.135 + 0.02], [0.155, 0.155, 0.155, 0.155], t_in=4.004, coord_out='rho_pol')
    rho = eqm.rz2rho([2.135 - 0.007, 2.135 + 0.008], [0.155, 0.155], t_in=4.004, coord_out='rho_pol')
