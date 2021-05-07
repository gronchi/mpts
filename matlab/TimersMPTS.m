function Timer=TimersMPTS(Trigger,ChargeOn,SimmerOn,PlotOn);
%                  
% M.Kantor version on 28.07.2016     
%===================================      
% 1. Return pulse timing of preparatoty cycle for multipass TS diagnostic in AUG
% 2. Time sequences of the pulses are calculated for 5 channels from input data. 
% 3. The channels are activated in accordance to the operation mode
% 4. All times in the preparatory cycle are counted from the first Pockels cell (PC)
%    trigger in laser burst 
% 5. Trigger is returned by TriggerMPTS.m

% Delay - time delays in timer units, 
% Start - absolute time of outputs from timers

% ChargeSet=[ChargeOn,AUGCharge]  
% ChargeOn -  1 - start from AUG, 0 - start manually
% AUGChargeStart, time of AUG TS0 pulse (us). AUGChargeDef=6e7; 

% SimmerSet=[SimmerOn,SimmerStart,SimmerWidth] 
% SimmerOn    1 in laser modes,  0 - operation without laser
% SimmerStart - start of the simmer current      1 in laser modes,  0 - operation without laser
%               SimmerOn=0 - no output
%               SimmerOn=1 
%                          ChargeOn=1  SimmerStart= f(1st PC, SimmerMinWait)
%                          ChargeOn=0  SimmerStart=0 

% BurstSet =[BurstOn,AUGShotStart]
% BurstOn -  1 - start from AUG, 0 - start from Simmer timer (manual start)
% AUGShotStart, time of T06 pulse (us). The pulse comes to Burst timer

% EnableSet =[EnableOn,EnableWidth]
% EnableOn -  1 - 
% EnableWidth - start of Enable output 
%              EnableOn=1: EnableStart =f(1st PC,AUTS0)
%              EnableOn=0: EnableStart =SimmerMinWait

% LaserTriggerSet =[LaserTriggerWidth]
% LaserTriggerWidth - start of LaserTrigger output 
%              LaserTriggerOn=1: LaserTriggerStart =f(1st PC,AUTS0)
%              LaserTriggerOn=0: LaserTriggerStart =SimmerMinWait


AUGChargeStart=-15e6; % us  , must be -60e6 us
AUGShotStart=Trigger.Burst.InTime; % us
TriggerMode=Trigger.TriggerMode;
PockelsFirstTime=Trigger.Pockels.PockelsFirstTime;
SimmerMinWait=Trigger.SimmerMinWait;

if nargin<2; ChargeOn=1; end; 
if nargin<3; SimmerOn=Trigger.Flash.On; end; 
 

ChargeInTime=0; ChargeWidth=100; ChargeDelay=0; 
ChargeBase=[[0,0]; [0,1]; [ChargeWidth,1]; [ChargeWidth,0]];
if ChargeOn 
   ChargeInTime= AUGChargeStart; 
end;
ChargeOutTime=ChargeInTime+ChargeDelay; 
Charge=ChargeBase;
Charge(:,1)=Charge(:,1)+ChargeOutTime;

SimmerWidth=100; 
if TriggerMode&ChargeOn  %Start from AUGShotStart 
   SimmerInTime=ChargeOutTime; 
   SimmerDelay=Trigger.Flash.InTime-SimmerInTime-SimmerMinWait; 
   SimmerOutTime=SimmerInTime+SimmerDelay;
else   % Manual simmer start
   SimmerDelay=0;  
   SimmerOutTime=Trigger.Burst.InTime;
   SimmerInTime=SimmerOutTime-SimmerDelay;
end; 

SimmerBase=[[0,0]; [0,1]; [SimmerWidth,1]; [SimmerWidth,0]];
Simmer=SimmerBase;
Simmer(:,1)=Simmer(:,1)+SimmerOutTime; 


BurstInTime=Trigger.Burst.InTime;
BurstN=Trigger.Burst.N; 
BurstDelay=Trigger.Burst.Delay;  
BurstOutTime=BurstInTime+BurstDelay;
BurstPeriod=Trigger.Burst.Period;
BurstWidth=Trigger.Burst.Width;
BurstBase=[[0,0]; [0,1]; [BurstWidth,1]; [BurstWidth,0]]; 
Burst=[];
for i=1:BurstN
    Burst=[Burst;[BurstBase(:,1)+(i-1)*BurstPeriod,BurstBase(:,2)]];    
end; 
if SimmerOn
    Burst(:,1)=Burst(:,1)+BurstOutTime;
end;

EnableOn=SimmerOn; EnableDelay=0; 
EnableInTime=SimmerOutTime;
EnableOutTime=EnableInTime+EnableDelay;
EnableWidth=BurstDelay+Trigger.Flash.Delay+Trigger.Pockels.Retard;   %+Trigger.Flash.OutTime
%EnableWidth=ceil((PockelsFirstTime+(BurstN-1)*BurstPeriod-EnableInTime)/1e5)*1e5;
EnableBase=[[0,0]; [0,1]; [EnableWidth,1]; [EnableWidth,0]];
Enable=EnableBase;
Enable(:,1)=Enable(:,1)+EnableOutTime;

LaserTriggerDelay=0; 
LaserTriggerInTime=EnableOutTime;
LaserTriggerOutTime=LaserTriggerInTime+LaserTriggerDelay;
LaserTriggerWidth=100; 
LaserTriggerBase=[[0,0];[0,1];[LaserTriggerWidth,1];[LaserTriggerWidth,0]]; 
LaserTrigger=LaserTriggerBase;
% start simmer current:
LaserTrigger(:,1)=LaserTrigger(:,1)+LaserTriggerOutTime;
% start flash current: 
LaserTrigger=[LaserTrigger;[0,0];[0,1];[LaserTriggerWidth,1];[LaserTriggerWidth,0]];
LaserTrigger(5:8,1)=LaserTrigger(5:8,1)+Trigger.Flash.OutTime;







% Outputs of timer channels: 
disp('  Channel   |   From     |      To           |Enable  |Delay(us) |Width(us)'); 
%Charge Timer: 
% Burst - grand parent:
Timer.Charge.On=ChargeOn; 
Timer.Charge.From='AUG|Man'; Timer.Charge.To='Charge&Simmer';
Timer.Charge.InTime=ChargeInTime;
Timer.Charge.OutTime=ChargeOutTime;
Timer.Charge.Delay=0;  Timer.Charge.Width=ChargeWidth; 
Timer.Charge.Period=0;  Timer.Charge.N=1; 
disp(['  Charge     ','|   ', Timer.Charge.From,'  | ', Timer.Charge.To,'       |   ',num2str(ChargeOn),'    |  '...
       0,'   |  ', num2str(ChargeWidth)]); 
% Simmer timer:
Timer.Simmer.On=SimmerOn; 
Timer.Simmer.From='Charge|Man'; Timer.Simmer.To='Burst&AND1'; 
Timer.Simmer.InTime=SimmerInTime;
Timer.Simmer.OutTime=SimmerOutTime;
Timer.Simmer.Delay=SimmerDelay;  Timer.Simmer.Width=SimmerWidth; 
Timer.Simmer.Period=0;  Timer.Simmer.N=1; 
disp(['  Simmer     ','|   ', Timer.Simmer.From,'    |', Timer.Simmer.To,'     |   ',num2str(SimmerOn),'    |  '...
       num2str(SimmerDelay),'     |  ', num2str(SimmerWidth)]); 

Timer.Enable.On=1; 
Timer.Enable.From='Simmer'; Timer.Enable.To='LaserTrigger'; 
Timer.Enable.InTime=EnableInTime;
Timer.Enable.OutTime=EnableOutTime;
Timer.Enable.Delay=0;  Timer.Enable.Width=EnableWidth;
Timer.Enable.Period=0;   Timer.Enable.N=1; 
disp([' Enable  ','|   ', Timer.Enable.From,'    |', Timer.Enable.To,'        |   ',num2str(1),'    |  '...
       num2str(0),'     |  ', num2str(EnableWidth)]); 

Timer.LaserTrigger.On=1; 
Timer.LaserTrigger.From='Enable&Flash'; Timer.LaserTrigger.To='Laser'; 
Timer.LaserTrigger.InTime=LaserTriggerInTime;
Timer.LaserTrigger.OutTime=LaserTriggerOutTime;
Timer.LaserTrigger.Delay=0;  
Timer.LaserTrigger.Width=LaserTriggerWidth;
Timer.LaserTrigger.Period=0;  Timer.LaserTrigger.N=1; 
disp([' LaserTrigger    ','|   ', Timer.LaserTrigger.From,'    |', Timer.LaserTrigger.To,'          |   ',num2str(1),'    |  '...
       num2str(0),'    |  ', num2str(LaserTriggerWidth)]); 


  
if PlotOn
  PlotN=5;   
 xmin=min([Simmer(1,1),Burst(1,1),Enable(1,1),LaserTrigger(1,1)])-round(Trigger.Pockels.Period);
 xmax=max([Simmer(end,1),Burst(end,1),Enable(end,1),LaserTrigger(end,1)])+round(Trigger.Pockels.Period);
  ymin=-0.1; ymax=1.1; 
          
  
  figure;   
  subplot(PlotN,1,1);
          if ChargeOn
          Charge=[[xmin,Charge(1,2)];Charge;[xmax,Charge(1,end)];];
          plot(1e-6*Charge(:,1),Charge(:,2),'k','Linewidth',2);  
          ylabel('Charge'); 
          title('Slow channels');
          end;
          axis([1e-6*xmin 1e-6*xmax ymin ymax]);
  subplot(PlotN,1,2);    
          if SimmerOn
          Simmer=[[xmin,Simmer(1,2)];Simmer;[xmax,Simmer(1,end)];];    
          plot(1e-6*Simmer(:,1),Simmer(:,2),'b','Linewidth',2);
          end; 
          axis([1e-6*xmin 1e-6*xmax ymin ymax]);  ylabel('Simmer'); 
  subplot(PlotN,1,3);    
          Burst=[[xmin,Burst(1,2)];Burst;[xmax,Burst(1,end)];];                  
          plot(1e-6*Burst(:,1),Burst(:,2),'r','Linewidth',2); 
          axis([1e-6*xmin 1e-6*xmax ymin ymax]);  ylabel('Burst');            
  subplot(PlotN,1,4);    
          Enable=[[xmin,Enable(1,2)];Enable;[xmax,Enable(1,end)];];                                
          plot(1e-6*Enable(:,1),Enable(:,2),'g','Linewidth',2);
          axis([1e-6*xmin 1e-6*xmax ymin ymax]);  ylabel('Enable');          
    subplot(PlotN,1,5);    
          if SimmerOn
          LaserTrigger=[[xmin,LaserTrigger(1,2)];LaserTrigger;[xmax,LaserTrigger(1,end)];];                                
          plot(1e-6*LaserTrigger(:,1),LaserTrigger(:,2),'c','Linewidth',2);
          end; 
          axis([1e-6*xmin 1e-6*xmax ymin ymax]);  ylabel('LaserTrigger');           
         
figure; hold on; 
plot(Charge(:,1),0.5*Charge(:,2),'k','Linewidth',2);  
plot(Simmer(:,1),1.2*Simmer(:,2),'b','Linewidth',2);
plot(Burst(:,1),1.2*Burst(:,2),'r','Linewidth',2);
plot(Enable(:,1),Enable(:,2),'g','Linewidth',2);
plot(LaserTrigger(:,1),0.8*LaserTrigger(:,2),'c','Linewidth',2);
   axis([xmin xmax 0,1.4]); xlabel('t, \mus');
legend('Charge','Simmer','Burst','Enable','LaserTrigger');    
end; 



  

