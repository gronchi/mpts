Trigger = TriggersMPTS([1,0], [1,100],[1,2.5e6,200,20,20,1400], [1,50, 10, 5,5,0], [1,0,10,10,5,2],[1,0,0.2e5],0)
Timer=TimersMPTS(Trigger,0,1,0);
CrioConfigFile(Trigger,Timer,'crioSettings_2.5s_50before.txt',0,1)
%%
% M2 (without laser), single camera
ChargeOn = 0; % start from manual
Trigger = TriggersMPTS([-1,0], [1,100],[1,1e6,200,20,20,1400], [1,50, 10, 5,5,0], [1,1,10,10,5,2],[1,-20000,0.1e5],1);
Timer=TimersMPTS(Trigger,0,0,0);
CrioConfigFile(Trigger,Timer,'crioSettings_1.0s_50before_M2_2cmos.txt',0,1);

