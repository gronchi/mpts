import MDSplus as mds
import matplotlib.pyplot as plt


# shot_number = 1408
# tree = mds.Tree("mpts_manual", shot_number)
shot_number = 38296
tree = mds.Tree("mpts", shot_number)

adc = tree.getNode("\\adc")
scope = tree.getNode("\\scope")
print(len(scope.CH1.SIGNAL.data()))
t_adc = adc.CH1.SIGNAL.dim_of().data()
t_scope = scope.CH1.SIGNAL.dim_of().data()
fig, ax = plt.subplots()

ax.plot(t_scope, scope.CH1.SIGNAL.data(), label="CH1")
ax.plot(t_scope, scope.CH2.SIGNAL.data(), label="CH2")
ax.plot(t_scope, scope.CH3.SIGNAL.data(), label="CH3")
ax.plot(t_scope, scope.CH4.SIGNAL.data(), label="CH4")
ax.plot(t_adc, adc.CH1.SIGNAL.data(), label="ADCCH1")
ax.plot(t_adc, adc.CH2.SIGNAL.data(), label="ADCCH1")
plt.legend()

plt.show()
