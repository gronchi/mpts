function [Trigger]=TriggersMPTS(TriggerSet,FlashSet,PockelsSet,IISet,CMOSSet,ADCSet,PlotOn);
% Trigger=TriggersMPTS([1,0], [1,100],[1,5.5e6,200,20,20,1500], [1,15, 10, 5,5,0], [1,0,10,10,5,2],[1,0,0.2e5],1)                  
% M.Kantor version on 28.07.2017     
%===================================      
% 1. Return pulse timing of measurement cycle for multipass TS diagnostic in AUG
% 2. Time sequences of the pulses are calculated for 8 channels from input
% data. 
% 3. The channels are activated in accordance to the operation mode
% 4. All times in the measurement cycle are counted from the first Pockels cell (PC)
%    trigger in laser burst
% InTime - absolute times of unit input
% OutTime - absolute times of unit output
% Delay - time delay between units outputs (Start) and unit input trigger 
%========================
% TriggerSet =[TriggerMode,AUGShotStart]
% FlashSet =[FlashOn, FlashWidth (us)]
% [PockelsOn,PockelsFirstTime (us),PockelsPeriod (us),PockelsN,
%       PockelsWidth (us),PockelsRetard (us)] 
% [IIOn,IIBeforeN, IIAfterN, IIGateLaserWidth (us), IIGatePlasmaWidth
%       (us),IIGateLaserFiberDelay (us)]
%[CMOSLaserOn,CMOSPlasmaOn, CMOSBeforeN, CMOSAfterN, CMOSTrigWidth (us), CMOSDeltaGate (us)];
%-================================


% TriggerSet =[TriggerMode,AUGShotStart]
% TriggerMode -  1 - Burst is started from AUG, T1 and T2 modes 
%                 0 - start from Simmer timer (manual start) (M1 and M2)
%                 -1  Start from Burst trigger (M2 mode without laser)
% AUGShotStart, time of AUG T06 pulse (us) which triggers Burst timer 

% FlashSet - array. 
% FlashSet =[FlashOn, FlashWidth (us)]
% FlashOn - Enable/disable of flash triggers        
% FlashWidth - the width of the flash trigger (us)

% PockelsSet - array: 
% [PockelsOn,PockelsFirstTime (us),PockelsPeriod (us),PockelsN, PockelsWidth (us),PockelsRetard (us)] 
% PockelsOn - Enable/disable of Pockels triggers
% PockelsFirstTime - time of the first PC pulse, us
% PockelsPeriod period of this pulses (us), 
% PockelsN the number of PC pulses, 
% PockelsWidth - duration of PC pulses (us),
% PockelsRetard - Delay of the 1st Pockels pulse after Flash


% IISet - array  
% [IIOn,IIBeforeN, IIAfterN, IIGateLaserWidth (us), IIGatePlasmaWidth (us),IIGateLaserFiberDelay (us)]
% IIOn - Enable/disable of the II triggers
% IIBeforeN - the number of twin pulses before PC pulses
% IIAfterN  - the number of twin pulses after PC pulses
% IIGateLaserWidth - GateLaser, duration of II gates during laser pulses(us), 
%               the first pulse in twins
% IIGatePlasmaWidth - GatePlasma, duration of II gate between laser pulses for pplasma light measurements (us)
%               the second pulse in twins
% IIGateLaserFiberDelay - fine delay of II gates triggered by the ruby laser via fiber for fine sinc of laser pulses. 
% The delay is also applicable for triggers from IIGatePlasma


% CMOSSet - array, settings triggeres for CMOS cameras 
% [CMOSLaserOn,CMOSPlasmaOn, CMOSBeforeN, CMOSAfterN, CMOSTrigWidth (us), CMOSDeltaGate (us)];
% CMOSLaserOn, CameraPlasmaOn - Enable/Disable switch of Camera1 and Camera2
% CMOSBeforeN - the number of twin CMOS pulses before the first II gate
% CMOSAfterN - the number of twin CMOS pulses after the last II gate
% CMOSTrigWidth - duration of trigger pulses of CMOS cameras, (us)
% CMOSDeltaGate - Difference between CMOS and II gates,CMOSDeltaGate>=0, us
%                  CMOSDeltaGate is set in the cameras  
% If two camears are active than the CMOSLaser trigger is generated
% for the 1st camera and the CMOSPlasma is generated for the 2nd camera
% Otherwise, all pulses are generated for a single camera

% ADCSet   array. The zero time is synchronized with the 1st PC pulses in the bursts 
%  [ADCOn,StartADC,StopADC]
%   StartADC - before the 1st PC, StopADC - after the 1st PC,  us
% if 1 then ADCSet is calculated from the pulse sequence

% Trigger times of Charge and Simmer timers are defined in Timers.m 

%==========================================================================
% Data range and defaults settings for timers  [Min,Step,Max,Default] 
%==========================================================================

% Operation modes: 

% T-modes   - TS is triggered from AUG
% AUG triggeres:  
% TZ60 - pretrigger at -60 s comes to Charge timer
% TS06 - start of plasma shot comes to Burst timer 
% SimmerTimer is triggered by delayed output of the Charge timer
% T1 mode: All three timers are disabled. 
%    Operator manually enables Charge timer before plasma shot
%    All timers are desibled after plasma shot
% T2 mode: Charge timer is enabled, Simmer and Burst are disabled 
%    Simmer and Burst are enabled by Charge trigger and disabled after
%    plasma shot 

% M-modes   - TS is triggered by operator without any AUG triggeres. 
% Laser charged by operator and Charge output does not trigger Simmer timer  
% Operation with laser is started from Simmer timer which triggeres Burst
% timer after some delay
% Operation without laser is started from Burst timer 
%          which cannot be triggered by Simmer timer. 
% All timers are enabled manually
% M1 mode: Manual trigger of the diagnostic without plasma 
%          (Rayleigh calibration, stray light measurements)
% M2 mode: Manual trigger of the diagnostic without laser 
%          (spectral calibrations,alignment of the cameras)
% M3 mode: Manual trigger of ruby laser 
%          without CMOS cameras and image intensifier. 



if nargin<7; PlotOn=1; end; 


% ====================================================
% Default values: 
  SimmerMinWait=3e6; % us minimal delay between simmer and flash triggers 
  TriggerModeDef=1; % 1 - Burst is started from AUG TS06 pulse, 
                     % 0 - start from Simmer timer (manual start)
                     
  
  % Laser defaults:
  FlashOnDef=1; 
  PockelsFirstTimeDef=0; % us, Absolute time of the 1st Pockels pulse
  PockelsWidthDef=10; % us 
  PockelsRetardDef=1000; % us, delay of the 1st Pockels pulse from the flash start  
  PockelsNDef=10; PockelsPeriodDef=200; % us
  PockelsDelayDef=round(PockelsPeriodDef/2); 
    
  
  % image intensifier defaults:  
  IIBeforeNDef=10; IIAfterNDef=20;
  IIGateLaserWidthDef=2; IIGatePlasmaWidthDef=20; 
  IIGateLaserFiberDelayDef=0; % us
  IIPlasmaRetardWidthDef=5; % us
  
  % CMOS defaults
  CMOSBeforeNDef=10; CMOSAfterNDef=20; 
  CMOSTrigWidthDef=5; % us
  CMOSDeltaGateDef=2; %us
      CMOSLaserGateDef =IIGateLaserWidthDef+CMOSDeltaGateDef;
      CMOSPlasmaGateDef=IIGatePlasmaWidthDef+CMOSDeltaGateDef;
  IIOnDef=1;  CMOSOnDef=[1,1];  
  
  
  %PockelsFirstTimeDef=(IIBeforeNDef+CMOSBeforeNDef)*PockelsPeriodDef;
  AUGShotStartDef=PockelsFirstTimeDef-(IIBeforeNDef+CMOSBeforeNDef)*PockelsPeriodDef; 
  if nargin==0|isempty(TriggerSet); AUGShotStart=AUGShotStartDef; end; % trigger from AUG 
   TriggerModeRange=[-1,1,1,TriggerModeDef];   
   
  SimmerDelayDef=PockelsFirstTimeDef-PockelsRetardDef; %SimmerMinWait; 
  SimmerInTimeDef=AUGShotStartDef-SimmerDelayDef;
  
% Burst, is triggered from AUG or Simmer timer. 
%        triggers Flash, IIGatePlasma,CMOSPlasmaOnRange and ADC
  % absolute time of output pulses from Burst timer: 
  MaxBeforeIntervalDef=max([(IIBeforeNDef+CMOSBeforeNDef+1)*PockelsPeriodDef,PockelsRetardDef])+PockelsPeriodDef; 

  
  if TriggerModeDef
     %Start from AUGShotStart 
     BurstInTimeDef=AUGShotStartDef;
  else 
     %Start form Simmer 
     BurstInTimeDef=0;  
  end;
    BurstDelayDef=SimmerMinWait; 
    BurstOutTimeDef=BurstInTimeDef+BurstDelayDef;
     
  BurstWidthDef=100;
  BurstPeriodDef=3e5;
  BurstNDef=1; 
 
  BurstDelayRange=[0,1000,10000000,BurstDelayDef]; % Delay of Burst output
  BurstPeriodRange=[1e5,1e5,1e7,BurstPeriodDef];  
  BurstWidthRange=[100,100,100,BurstWidthDef]; 
  BurstNRange=[1,1,4,BurstNDef]; 
  
% Laser times  
% Flash, pulses starting flash discharge. One per a pulse from Burst timer
% absolute time of output pulses from Burst trigger:
     FlashOutTimeDef=PockelsFirstTimeDef-PockelsRetardDef;
  %Delay between output and input triggers: 
  FlashDelayDef=FlashOutTimeDef-BurstOutTimeDef;  
  FlashInTimeDef=BurstOutTimeDef; 
  FlashOnRange=[0,1,1,FlashOnDef];  
  FlashDelayRange=[0,10,10000,FlashDelayDef]; % Delay of Flash output
  FlashPeriodRange=[0,0,0,0];  FlashWidthRange=[50,50,200,100]; 
  FlashNRange=[1,1,1,1]; 
% FlashBool,  Gate of all Pockels pulses. Triggered by Flash
% absolute time of output pulses from Flash trigger:
      FlashBoolOutTimeDef=fix((PockelsFirstTimeDef-PockelsPeriodDef/2)/10)*10;
  %Delay between output and input triggers: 
  FlashBoolDelayDef=FlashBoolOutTimeDef-FlashInTimeDef;  
  
  FlashBoolWidthDef=fix((PockelsNDef+1)*PockelsPeriodDef/10)*10;
  FlashBoolOnRange=[1,1,1,FlashOnDef];  
  FlashBoolDelayRange=[0,10,10000,FlashBoolDelayDef];
  FlashBoolPeriodRange=[0,0,0,0]; 
  FlashBoolWidthRange=[1,10,10000,FlashBoolWidthDef]; 
  FlashBoolNRange=[1,1,1,1]; 
% Pockels, Gates of Pockels cell. Reapeted in each burst. Triggered by Flash 
% absolute time of the 1st output pulse from Pockels trigger: 
  
  PockelsOnRange=[0,1,1,FlashOnDef];  
  %Delay between output and input triggers: 
  PockelsRetardDef=PockelsFirstTimeDef-FlashInTimeDef;   
  PockelsRetardRange=[0,1,10000,PockelsRetardDef];
  PockelsPeriodRange=[50,25,1000,PockelsPeriodDef]; PockelsWidthRange=[1,1,30,PockelsWidthDef]; 
  PockelsNRange=[0,1,100,PockelsNDef]; 
  

% II times:   
% IIPlasmaRetard, Trigger of IIGatesLaser. Triggered by IIGatePlasma 
% absolute time of output pulse from IIPlasmaRetard:
  IIPlasmaRetardOutTimeDef=PockelsFirstTimeDef+PockelsWidthDef-IIGateLaserWidthDef-IIBeforeNDef*PockelsPeriodDef;   
% Delay between starts of plasma and laser II gates:
  IIPlasmaRetardDelayDef=fix((PockelsPeriodDef+IIGatePlasmaWidthDef-IIGateLaserWidthDef)/2); % us
  IIPlasmaRetardOnRange=[1,1,1,1]; 
  IIPlasmaRetardDelayRange=[0,0.1,2000,IIPlasmaRetardDelayDef]; 
  IIPlasmaRetardPeriodRange=[0,0,0,0];  IIPlasmaRetardWidthRange=[1,1,5,IIPlasmaRetardWidthDef];
  IIPlasmaRetardNRange=[1,1,1,1];          

% IIGatePlasma, Gates of image intensifier between pockels gates. Triggered by Burst timer  
% absolute time of output pulses from IIGatePlasma:
  IIGatePlasmaOutTimeDef=PockelsFirstTimeDef+PockelsWidthDef-IIGateLaserWidthDef...
          -IIBeforeNDef*PockelsPeriodDef-IIPlasmaRetardDelayDef;  
  %Delay between output and input triggers: 
  IIGatePlasmaDelayDef=IIGatePlasmaOutTimeDef-BurstOutTimeDef;  
  IIGatePlasmaOnRange=[0,1,1,IIOnDef];  
  IIGatePlasmaDelayRange=[0,1,100000,IIGatePlasmaDelayDef]; 
  IIGatePlasmaPeriodRange=PockelsPeriodRange; IIGatePlasmaWidthRange=[1,1,100,IIGatePlasmaWidthDef];  % formulas
  IIGatePlasmaNRange=[0,1,100,PockelsNDef+IIBeforeNDef+IIAfterNDef];    
  
% IIGateLaser, Gate of image intensifier triggered by IIPlasmaRetard or
%              external laser trigger
% absolute time of output pulses from IIGateLaser:
  %IIGateLaserOutTimeDef=IIPlasmaRetardOutTimeDef; 
  
  %Delay between output and input triggers:
  IIGateLaserDelayDef=0; %IIGateLaserOutTimeDef-IIPlasmaRetardOutTimeDef;
  IIGateLaserOnRange=[0,1,1,IIOnDef]; 
  IIGateLaserDelayRange=[0,0.1,5,IIGateLaserDelayDef]; 
  IIGateLaserPeriodRange=[0,0,0,0]; IIGateLaserWidthRange=[0.1,0.1,10,IIGateLaserWidthDef]; 
  IIGateLaserNRange=[1,1,1,1];     

% Sum of IIGateLaser and IIGatePlasma 
% IIGate = IIGateLaser | IIGatePlasma

% CMOS times: 
% CMOSLaser trigger of Laser CMOS  
% absolute time of output pulse from CMOSLaser:
  CMOSLaserOutTimeDef= PockelsFirstTimeDef+PockelsWidthDef-IIGateLaserWidthDef...
                     -IIBeforeNDef*PockelsPeriodDef;
                       
% Delay between output and input triggers:
  CMOSLaserDelayDef=fix((PockelsPeriodDef+CMOSPlasmaGateDef-CMOSLaserGateDef)/2); % us
  CMOSLaserOnRange=[1,1,1,1]; 
  CMOSLaserDelayRange=[0,1,2000,CMOSLaserDelayDef]; % Delay after CMOSGateLaser 
  CMOSLaserPeriodRange=[0,0,0,0]; CMOSLaserGateRange=[1,1,5,CMOSTrigWidthDef];
  CMOSLaserNRange=[1,1,1,1];  

% CMOSPlasma, Pulses opening Plasma CMOS camera and triggered by Burst timer: 
%         The exposure time is set by the camera software
% absolute time of output pulse from CMOSPlasma:
  CMOSPlasmaOutTimeDef=CMOSLaserOutTimeDef-CMOSLaserDelayDef;   % wrong?
  CMOSPlasmaOutTimeDef=IIGatePlasmaOutTimeDef-IIGatePlasmaDelayDef-fix(CMOSDeltaGateDef/2)-CMOSTrigWidthDef;
%Delay between output and input triggers: 
  CMOSPlasmaDelayDef=CMOSPlasmaOutTimeDef-BurstOutTimeDef;     % wrong?
  CMOSPlasmaOnRange=[0,1,1,CMOSOnDef(1)|CMOSOnDef(2)]; 
  CMOSPlasmaDelayRange=[0,1,10000,CMOSPlasmaDelayDef]; 
  CMOSPlasmaPeriodRange=PockelsPeriodRange;  CMOSPlasmaGateRange=[1,1,50,CMOSTrigWidthDef];   % formulas
  CMOSPlasmaNRange=[0,1,100,PockelsNDef+IIBeforeNDef+IIAfterNDef+CMOSBeforeNDef+CMOSAfterNDef];     
  

% ADC  
% absolute time of output pulses from ADC:
  ADCStartDef=min([FlashInTimeDef,IIGatePlasmaOutTimeDef,CMOSPlasmaOutTimeDef]); 
  ADCDelayDef=max(0,ADCStartDef-BurstOutTimeDef);
  ADCWidthDef=(PockelsNDef+IIBeforeNDef+IIAfterNDef+CMOSBeforeNDef+CMOSAfterNDef)*PockelsPeriodDef; 
  ADCOnRange=[0,1,1,1];  ADCStartRange=[-5000,10,0,ADCDelayDef]; 
  ADCPeriodRange=[0,0,0,0]; ADCWidthRange=[100,100,50000,ADCWidthDef];  
  ADCNRange=FlashNRange; 
% end Default values
% ==============================


%==========================================================================  
% Read input data: 
%==========================================================================
%Readout Pockels =======================================  
 PockelsOn=PockelsOnRange(4); PockelsFirstTime=PockelsFirstTimeDef;
 PockelsPeriod=PockelsPeriodRange(4);
 PockelsWidth=PockelsWidthRange(4);  
 PockelsN=PockelsNRange(4); PockelsRetard=PockelsRetardRange(4); 
if nargin>2
   if not(isempty(PockelsSet))
   PockelsOn=PockelsSet(1); PockelsFirstTime=PockelsSet(2);
   PockelsPeriod=PockelsSet(3); PockelsN=PockelsSet(4); 
   PockelsWidth=PockelsSet(5); PockelsRetard=PockelsSet(6);     
end; end; 

%Readout Flash ======================================
 FlashOn=FlashOnRange(4); FlashDelay=FlashDelayRange(4); 
 FlashPeriod=FlashPeriodRange(4); FlashWidth=FlashWidthRange(4);  
 FlashN=FlashNRange(4);
if nargin>1
   if not(isempty(FlashSet)) 
   FlashOn=FlashSet(1);FlashWidth=FlashSet(2);
end; end;

%Readout II =======================================
% IIGatePlasma:  
 IIOn=IIOnDef;
 IIGatePlasmaOn=IIOn; IIGatePlasmaPeriod=IIGatePlasmaPeriodRange(4); 
 IIGatePlasmaWidth=IIGatePlasmaWidthRange(4);  
 IIGatePlasmaN=IIGatePlasmaNRange(4);
 IIBeforeN=IIBeforeNDef; IIAfterN=IIAfterNDef; 
  IIPlasmaRetardOn=1;  IIPlasmaRetardWidth=IIPlasmaRetardWidthRange(4);
  IIPlasmaRetardDelay=IIPlasmaRetardDelayRange(4);
  IIPlasmaRetardN=1;   IIPlasmaRetardPeriod=IIPlasmaRetardPeriodRange(4); 
 IIGateLaserOn=IIOn;  
 IIGateLaserWidth=IIGateLaserWidthRange(4);  
 IIGateLaserPeriod=IIGateLaserPeriodRange(4);
 IIGateLaserN=1;  
if nargin>3
    if not(isempty(IISet))
    IIOn=IISet(1);
    IIGatePlasmaOn=IIOn; IIGateLaserOn=IIOn; 
    IIBeforeN=IISet(2); IIAfterN=IISet(3); 
    IIGateLaserWidth=IISet(4); IIGatePlasmaWidth=IISet(5); 
    IIGateLaserFiberDelay=IISet(6);     
    IIGatePlasmaPeriod=PockelsPeriod;
    IIGatePlasmaN=IIBeforeN+IIAfterN+PockelsN;
    IIPlasmaRetardDelay=fix((PockelsPeriod+IIGatePlasmaWidth-IIGateLaserWidth)/2); % us    
end; end;
% IIPlasmaRetard 
  
   
%Readout CMOS =======================================
% CMOSPlasma
 CMOSLaserOn=CMOSOnDef(1); CMOSPlasmaOn=CMOSOnDef(2); 
 CMOSPlasmaPeriod=PockelsPeriodRange(4);   
 CMOSPlasmaN=CMOSPlasmaNRange(4); 
 CMOSLaserN=1;   CMOSLaserPeriod=CMOSLaserPeriodRange(4);  
 CMOSTrigWidth=CMOSTrigWidthDef;
 CMOSDeltaGate=CMOSDeltaGateDef;
 CMOSBeforeN=CMOSBeforeNDef;
 CMOSAfterN=CMOSAfterNDef;
 
 CMOSLaserGate=IIGateLaserWidth+CMOSDeltaGate;
 CMOSPlasmaGate=IIGatePlasmaWidth+CMOSDeltaGate;
 % Delay between output and input triggers:
if nargin>4
    if not(isempty(CMOSSet))
    CMOSLaserOn=CMOSSet(1); CMOSPlasmaOn=CMOSSet(2); 
    CMOSBeforeN=CMOSSet(3); CMOSAfterN=CMOSSet(4);
    CMOSTrigWidth=CMOSSet(5); CMOSDeltaGate=CMOSSet(6);
    CMOSLaserGate=IIGateLaserWidth+CMOSDeltaGate;
    CMOSPlasmaGate=IIGatePlasmaWidth+CMOSDeltaGate;
    CMOSPlasmaN=CMOSBeforeN+CMOSAfterN+IIBeforeN+IIAfterN+PockelsN;
    CMOSPlasmaPeriod=PockelsPeriod; 
end; end; 

if not(CMOSLaserOn&CMOSPlasmaOn)
    CMOSMaxWidth=max([CMOSLaserGate,CMOSPlasmaGate]); 
    CMOSLaserGate=CMOSMaxWidth;CMOSPlasmaGate=CMOSMaxWidth;
end; 

%Readout ADC ============================================
 ADCOn=ADCOnRange(4); ADCStart=ADCStartRange(4); 
 ADCPeriod=ADCPeriodRange(4); ADCWidth=ADCWidthRange(4);  
 ADCN=ADCNRange(4);
 ADCStart=ADCStartDef;
 ADCWidth=ADCWidthDef;
if nargin>5
   if not(isempty(ADCSet)) 
   ADCOn=ADCSet(1);
   if length(ADCSet)==3
      ADCStart=ADCSet(2);    
      ADCWidth=ADCSet(3)-ADCSet(2); 
   else  ADCStart=0; ADCWidth=0;   end;
end; end;

%Readout Burst =========================================================== 
 TriggerMode=TriggerModeRange(4);
 AUGShotStart=AUGShotStartDef;
 BurstWidth=BurstWidthDef;
 BurstPeriod=BurstPeriodDef; 
 BurstN=BurstNDef;
 if nargin>0
    if not(isempty(TriggerSet)) 
      TriggerMode=TriggerSet(1); AUGShotStart=TriggerSet(2);  
      if TriggerMode==1 %(start from AUG)
          AUGShotStart=TriggerSet(2);
      else
          AUGShotStart=0; SimmerMinWait+PockelsRetard; %(Start from Simmer)
      end;
      BurstPeriod=BurstPeriodRange(4);
      BurstWidth=BurstWidthRange(4);  
      BurstN=BurstNRange(4); 
 end; end;
 BurstOn=1; 

 FlashBoolOn=FlashOn; FlashBoolN=BurstN; 
 FlashBoolPeriod=BurstPeriod;
 FlashBoolWidth=fix(PockelsN*PockelsPeriod/10)*10; 
 
%=======================================================
% Absolute times of input triggers: 
%=======================================================

%FlashInTime=PockelsFirstTime-PockelsRetard;
%FlashInTime=PockelsFirstTime-PockelsRetard-FlashDelay; % ok

MaxBeforeInterval=max([-ADCSet(2),(IIBeforeN+CMOSBeforeN+1)*PockelsPeriod,PockelsRetard])+PockelsPeriod;

if TriggerMode % start from AUG (T modes)
   BurstInTime=AUGShotStart;
   BurstDelay=BurstInTime-AUGShotStart;    % wrong
   
else    % Start from Simmer (manual modes)
   BurstInTime=0; 
   BurstDelay=SimmerMinWait; 
end; 
BurstOutTime=BurstInTime+BurstDelay;

PockelsFirstTimeMin=BurstOutTime+MaxBeforeInterval; 
PockelsFirstTimeDelta=PockelsFirstTimeMin-PockelsFirstTime; 
PockelsFirstTime=max([PockelsFirstTimeMin,PockelsFirstTime]);
PockelsFirstTimeDelta=max([PockelsFirstTimeDelta,0]);

FlashOutTime=PockelsFirstTime-PockelsRetard;
FlashInTime=BurstOutTime;
FlashDelay=FlashOutTime-FlashInTime;

PockelsInTime=FlashOutTime;

FlashBoolOutTime=fix(PockelsFirstTime-PockelsPeriod/2); 
FlashBoolInTime=FlashOutTime;
FlashBoolDelay=FlashBoolOutTime-FlashBoolInTime;   

IIGatePlasmaInTime=BurstOutTime;
IIGatePlasmaOutTime=PockelsFirstTime+PockelsWidth-IIGateLaserWidth...
                     -IIBeforeN*PockelsPeriod-IIPlasmaRetardDelay;  
IIGatePlasmaDelay=IIGatePlasmaOutTime-IIGatePlasmaInTime;   

IIPlasmaRetardInTime=IIGatePlasmaOutTime; 
IIPlasmaRetardOutTime=IIPlasmaRetardInTime+IIPlasmaRetardDelay;

IIGateLaserInTime=IIPlasmaRetardOutTime;
IIGateLaserOutTime=PockelsFirstTime+PockelsWidth-IIGateLaserWidth...
                     -IIBeforeN*PockelsPeriod;  
IIGateLaserDelay=IIGateLaserOutTime- IIGateLaserInTime;                


CMOSLaserOutTime= IIGateLaserOutTime-CMOSTrigWidth-(PockelsWidth-IIGateLaserWidth)-...
      fix(CMOSDeltaGate/2)-(CMOSBeforeN)*PockelsPeriod;
CMOSLaserDelay=fix((PockelsPeriod+CMOSPlasmaGate-CMOSLaserGate)/2); 
CMOSLaserInTime=CMOSLaserOutTime-CMOSLaserDelay;

CMOSPlasmaOutTime=CMOSLaserInTime; 
CMOSPlasmaDelay=CMOSPlasmaOutTime-BurstOutTime;
CMOSPlasmaInTime=CMOSPlasmaOutTime- CMOSPlasmaDelay;




%==========================================================================
% settings basic pulses which are repeatedly generated  
% There are four parent triggeres which are started by the Burst timer: 
%   Flash, IIGatePlasma, CMOSPlasma and ADC
% Other triggeres are started by the parent outputs
% times of parent triggers are counted from the output of the Burst timer.
%==========================================================================
% Burst - grand parent: 
  BurstBase=[[0,0]; [0,1]; [BurstWidth,1]; [BurstWidth,0]];
  Burst=BurstBase;
  BurstTimeWindow=[Burst(1,1),Burst(end,1)];    
  FlashBase=[[0,0]; [0,1]; [FlashWidth,1]; [FlashWidth,0]];
  FlashBoolBase=[[0,0]; [0,1]; [FlashBoolWidth,1]; [FlashBoolWidth,0]]; 
  PockelsBase=[[0,0];  [0,1]; [PockelsWidth,1]; [PockelsWidth,0]];


  IIGatePlasmaBase=[[0,0]; [0,1]; [IIGatePlasmaWidth,1];  [IIGatePlasmaWidth,0]]; 
  IIPlasmaRetardBase=[[0,0]; [0,1]; [IIPlasmaRetardWidth,1];  [IIPlasmaRetardWidth,0]]; 
  IIGateLaserBase=[[0,0]; [0,1]; [IIGateLaserWidth,1];  [IIGateLaserWidth,0]];  
  
%==========================================================================  
  


%==========================================================================
% Time sequences from triggers:
%==========================================================================  
% Flash is triggered by Burst: 
Flash=FlashBase;  % single pulse
Flash(:,1)=Flash(:,1)+FlashInTime+FlashDelay;
FlashBool=FlashBoolBase; % single pulse
FlashBool(:,1)=FlashBool(:,1)+FlashBoolOutTime;
Pockels=[]; 
for i=1:PockelsN;
    Pockels=[Pockels;[PockelsBase(:,1)+(i-1)*PockelsPeriod,PockelsBase(:,2)]];
end; 
if PockelsFirstTime==FlashInTime+FlashDelay+PockelsRetard;
   Pockels(:,1)=Pockels(:,1)+PockelsFirstTime;
else 
   error('PockelsFirstTime'); 
end; 
LaserTimeWindow=[Flash(1,1),Pockels(end,1)+PockelsWidth]; 

% IIGatePlasma is triggered by Flash: 
IIGatePlasma=[]; IIPlasmaRetard=[]; IIGateLaser=[]; 
for i=1:(IIBeforeN+PockelsN+IIAfterN);
    IIGatePlasma=[IIGatePlasma;[IIGatePlasmaBase(:,1)+(i-1)*PockelsPeriod,IIGatePlasmaBase(:,2)]];
    IIPlasmaRetard=[IIPlasmaRetard;[IIPlasmaRetardBase(:,1)+(i-1)*PockelsPeriod,IIPlasmaRetardBase(:,2)]];
    IIGateLaser=[IIGateLaser;[IIGateLaserBase(:,1)+(i-1)*PockelsPeriod,IIGateLaserBase(:,2)]];
end;    

if IIGatePlasmaOutTime==BurstOutTime+IIGatePlasmaDelay;
   IIGatePlasma(:,1)=IIGatePlasma(:,1)+IIGatePlasmaOutTime;
else
    error('IIGatePlasmaOutTime'); 
end;
if IIPlasmaRetardOutTime==IIGatePlasmaOutTime+IIPlasmaRetardDelay;
   IIPlasmaRetard(:,1)=IIPlasmaRetard(:,1)+IIPlasmaRetardOutTime;
else
    error('IIPlasmaRetardOutTime'); 
end;
if IIGateLaserOutTime==BurstOutTime+IIGatePlasmaDelay+IIPlasmaRetardDelay;
   IIGateLaser(:,1)=IIGateLaser(:,1)+IIGateLaserOutTime;
else
   error('IIGateLaserOutTime');
end;
%IIGateLaser(IIGateLaser(:,1)>FlashBool(1,1)&IIGateLaser(:,1)<FlashBool(end,1),2)=0; 

IITimeWindow=[IIGatePlasma(1,1),IIGateLaser(end,1)+IIGateLaserWidth];                                         

  
% CMOSPlasma is triggered by Flash: 
CMOSPlasmaBase=[[0,0]; [0,1]; [CMOSTrigWidth,1];  [CMOSTrigWidth,0]]; 
CMOSLaserBase=[[0,0]; [0,1]; [CMOSTrigWidth,1];  [CMOSTrigWidth,0]];
CMOSLaser=[]; CMOSPlasma=[]; %CMOSPlasmaRetard=[]; 
for i=1:(CMOSBeforeN+IIBeforeN+PockelsN+IIAfterN+CMOSAfterN);
    CMOSPlasma=[CMOSPlasma;[CMOSPlasmaBase(:,1)+(i-1)*PockelsPeriod,CMOSPlasmaBase(:,2)]];
%    CMOSPlasmaRetard=[CMOSPlasmaRetard;[CMOSPlasmaRetardBase(:,1)+(i-1)*PockelsPeriod,CMOSPlasmaRetardBase(:,2)]];
    CMOSLaser=[CMOSLaser;[CMOSLaserBase(:,1)+(i-1)*PockelsPeriod,CMOSLaserBase(:,2)]];
end;   
CMOSPlasma(:,1)=CMOSPlasma(:,1)+CMOSPlasmaOutTime;
CMOSLaser(:,1)=CMOSLaser(:,1)+CMOSLaserOutTime; 



CMOSTimeWindow=[CMOSPlasma(1,1),CMOSLaser(end,1)+CMOSLaserGate];     

% ADC:
ADCInTime=BurstOutTime;
ADCOutTime=PockelsFirstTime+ADCStart;
ADCDelay=ADCOutTime-ADCInTime;   %ADCDelayDef; 
ADC=[[0,0]; [0,1]; [ADCWidth,1];  [ADCWidth,0]];
ADC(:,1)=ADC(:,1)+ADCOutTime;  
if ADCStart==0&ADCWidth==0
  ADCStart=CMOSTimeWindow(1); 
  ADCWidth= CMOSTimeWindow(2)-ADCStart;
  ADCDelay=ADCStart-BurstInTime; 
  ADC=[[0,0]; [0,1]; [ADCWidth,1];  [ADCWidth,0]];
  ADC(:,1)=ADC(:,1)+ADCStart;  

end; 


% Outputs of trigger channels: 
disp('  Channel   |   From     |      To           |Enable  |Delay(us) |Period(us)|  Number  |Width(us)'); 

%Burst Timer: 
% Burst - grand parent:

Trigger.Burst.On=BurstOn;  
Trigger.Burst.From='T0orSimm'; Trigger.Burst.To='Four trigg'; 
Trigger.Burst.InTime=BurstInTime; 
Trigger.Burst.OutTime=BurstOutTime;
Trigger.Burst.Delay=BurstDelay; 
Trigger.Burst.Width=BurstWidth; Trigger.Burst.Period=BurstPeriod;  
Trigger.Burst.N=BurstN; 
disp(['  Burst     ','|   ', Trigger.Burst.From,'  | ', Trigger.Burst.To,'       |   ',num2str(TriggerMode),'    |  '...
       num2str(BurstDelay),'   |  ',num2str(BurstPeriod),'  |    ',num2str(BurstN),'     |  ', num2str(BurstWidth)]); 


if Trigger.Burst.OutTime==FlashInTime
Trigger.Flash.From='Burst'; Trigger.Flash.To='FlashBool&Pock'; 
Trigger.Flash.InTime=FlashInTime;
Trigger.Flash.OutTime=FlashOutTime;
Trigger.Flash.Delay=FlashDelay;  
Trigger.Flash.Width=FlashWidth; 
Trigger.Flash.Period=FlashPeriod;  Trigger.Flash.N=FlashN;
else
    error('Error: Trigger.Burst.OutTime<>FlashInTime');
end;
disp(['  Flash     ','|   ', Trigger.Flash.From,'    |', Trigger.Flash.To,'     |   ',num2str(FlashOn),'    |  '...
       num2str(FlashDelay),'   |    ',num2str(FlashPeriod),'     |    ',num2str(FlashN),'     |  ', num2str(FlashWidth)]); 

if Trigger.Flash.OutTime==FlashBoolInTime
Trigger.FlashBool.From='Flash'; Trigger.FlashBool.To='IIGateLaser'; 
Trigger.FlashBool.InTime=FlashBoolInTime;
Trigger.FlashBool.OutTime=FlashBoolOutTime;
Trigger.FlashBool.Delay=FlashBoolDelay;  
Trigger.FlashBool.Width=FlashBoolWidth;
Trigger.FlashBool.Period=FlashBoolPeriod;  Trigger.FlashBool.N=1; 
else
    error('Error: Trigger.Flash.OutTime<>FlashBoolInTime');
end;

disp([' FlashBool  ','|   ', Trigger.FlashBool.From,'    |', Trigger.FlashBool.To,'        |   ',num2str(FlashBoolOn),'    |  '...
       num2str(FlashBoolDelay),'    |    ',num2str(FlashBoolPeriod),'     |    ',num2str(FlashBoolN),'     |  ', num2str(FlashBoolWidth)]); 

if Trigger.Flash.OutTime==PockelsInTime   
Trigger.Pockels.From='Flash'; Trigger.Pockels.To='Pock cell'; 
Trigger.Pockels.InTime=PockelsInTime; 
Trigger.Pockels.PockelsFirstTime=PockelsFirstTime;  % OutTime
Trigger.Pockels.Retard=PockelsRetard;     % Delay  
Trigger.Pockels.Width=PockelsWidth;
Trigger.Pockels.Period=PockelsPeriod;  Trigger.Pockels.N=PockelsN; 
else
    error('Error: Trigger.Flash.OutTime<>PockelsInTime');
end;



disp([' Pockels    ','|   ', Trigger.Pockels.From,'    |', Trigger.Pockels.To,'          |   ',num2str(PockelsOn),'    |  '...
       num2str(PockelsRetard),'   |    ',num2str(PockelsPeriod),'   |    ',num2str(PockelsN),'    |  ', num2str(PockelsWidth)]); 

if Trigger.Burst.OutTime==IIGatePlasmaInTime
Trigger.IIGatePlasma.From='Burst'; Trigger.IIGatePlasma.To='IIGate(2)&IIPlRetrd'; 
Trigger.IIGatePlasma.InTime=IIGatePlasmaInTime;
Trigger.IIGatePlasma.OutTime=IIGatePlasmaOutTime;
Trigger.IIGatePlasma.Delay=IIGatePlasmaDelay; 
Trigger.IIGatePlasma.Width=IIGatePlasmaWidth;
Trigger.IIGatePlasma.Period=IIGatePlasmaPeriod;   Trigger.IIGatePlasma.N=IIGatePlasmaN; 
else
    error('Error: Trigger.Burst.OutTime<>IIGatePlasmaInTime');
end;

disp(['IIGatePlasma','|   ', Trigger.IIGatePlasma.From,'    |', Trigger.IIGatePlasma.To,'|   ',num2str(IIGatePlasmaOn),'    |  '...
       num2str(IIGatePlasmaDelay),'   |    ',num2str(IIGatePlasmaPeriod),'   |    ',num2str(IIGatePlasmaN),'    |  ', num2str(IIGatePlasmaWidth)]); 

if Trigger.IIGatePlasma.OutTime==IIPlasmaRetardInTime
Trigger.IIPlasmaRetard.From='IIGatePlasma'; Trigger.IIPlasmaRetard.To='IIGateLaser'; 
Trigger.IIPlasmaRetard.InTime=IIPlasmaRetardInTime;
Trigger.IIPlasmaRetard.OutTime=IIPlasmaRetardOutTime;
Trigger.IIPlasmaRetard.Delay=IIPlasmaRetardDelay;  % Check this
Trigger.IIPlasmaRetard.Width=IIPlasmaRetardWidth;
Trigger.IIPlasmaRetard.Period=IIPlasmaRetardPeriod; Trigger.IIPlasmaRetard.N=IIPlasmaRetardN; 
else
    error('Error: Trigger.IIGatePlasma.OutTime<>IIPlasmaRetardInTime');
end;

disp(['IIPlasmaRet ','|', Trigger.IIPlasmaRetard.From,'|    ', Trigger.IIPlasmaRetard.To,'    |   ',num2str(IIPlasmaRetardOn),'    |  '...
       num2str(IIPlasmaRetardDelay),'   |    ',num2str(IIPlasmaRetardPeriod),'     |    ',num2str(IIPlasmaRetardN),'     |  ', num2str(IIPlasmaRetardWidth)]); 

if Trigger.IIPlasmaRetard.OutTime==IIGateLaserInTime  
Trigger.IIGateLaser.From='FlashBool,IIPlRet,LaserPuls'; Trigger.IIGateLaser.To='IIGates(1)'; 
Trigger.IIGateLaser.InTime=IIGateLaserInTime;
Trigger.IIGateLaser.OutTime=IIGateLaserOutTime;
Trigger.IIGateLaser.Delay=IIGateLaserDelay; 
Trigger.IIGateLaser.FiberDelay=IIGateLaserFiberDelay; 
Trigger.IIGateLaser.Width=IIGateLaserWidth;
Trigger.IIGateLaser.Period=IIGateLaserPeriod;  Trigger.IIGateLaser.N=IIGateLaserN;
else
    error('Error: Trigger.IIGatePlasma.OutTime<>IIPlasmaRetardInTime');
end;
disp(['IIGateLaser ','|', ' FlashBool  ','|    ', Trigger.IIGateLaser.To,'     |   ',num2str(IIGateLaserOn),'    |  '...
       num2str(IIGateLaserDelay),'   |    ',num2str(IIGateLaserPeriod),'     |    ',num2str(IIGateLaserN),'     |  ', num2str(IIGateLaserWidth)]); 
disp(['            |IIPlRet&LasPuls|                           ']);   


if Trigger.Burst.OutTime==CMOSPlasmaInTime
Trigger.CMOSPlasma.On=CMOSPlasmaOn;    
Trigger.CMOSPlasma.From='Burst'; Trigger.CMOSPlasma.To='CMOSTr(2),CMOSPlRet'; 
Trigger.CMOSPlasma.InTime=CMOSPlasmaInTime;
Trigger.CMOSPlasma.OutTime=CMOSPlasmaOutTime;
Trigger.CMOSPlasma.Delay=CMOSPlasmaDelay;  
Trigger.CMOSPlasma.Width=CMOSTrigWidth; 
Trigger.CMOSPlasma.Period=CMOSPlasmaPeriod; Trigger.CMOSPlasma.N=CMOSPlasmaN; 
Trigger.CMOSPlasma.Gate=CMOSPlasmaGate;
else
   error('Error: Trigger.Burst.OutTime<>CMOSPlasmaInTime') 
end

disp(['CMOSPlasma','  |   ', Trigger.CMOSPlasma.From,'    |', Trigger.CMOSPlasma.To,'|   ',num2str(CMOSPlasmaOn),'    |  '...
       num2str(CMOSPlasmaDelay),'   |    ',num2str(CMOSPlasmaPeriod),'   |    ',num2str(CMOSPlasmaN),'    |  ', num2str(CMOSTrigWidth)]); 

if Trigger.CMOSPlasma.OutTime==CMOSLaserInTime
Trigger.CMOSLaser.On=CMOSLaserOn;    
Trigger.CMOSLaser.From='CMOSPlRetrd'; Trigger.CMOSLaser.To='CMOSTrigger(1)'; 
Trigger.CMOSLaser.InTime=CMOSLaserInTime;
Trigger.CMOSLaser.OutTime=CMOSLaserOutTime;
Trigger.CMOSLaser.Delay=CMOSLaserDelay; 
Trigger.CMOSLaser.Width=CMOSTrigWidth; 
Trigger.CMOSLaser.Period=CMOSLaserPeriod;  Trigger.CMOSLaser.N=CMOSLaserN; 
Trigger.CMOSLaser.Gate=CMOSLaserGate;
else
   error('Error: Trigger.CMOSPlasma.OutTime<>CMOSLaserInTime') 
end

Trigger.SimmerMinWait=SimmerMinWait;
Trigger.TriggerMode=TriggerMode;

disp(['CMOSLaser','   | ', Trigger.CMOSLaser.From,'|   ', Trigger.CMOSLaser.To,'  |   ',num2str(CMOSLaserOn),'    |  '...
       num2str(CMOSLaserDelay),'   |    ',num2str(CMOSLaserPeriod),'     |    ',num2str(CMOSLaserN),'     |  ', num2str(CMOSTrigWidth)]); 

   
%ADC parent: 
Trigger.ADC.From='Burst'; Trigger.ADC.To='Digitizer'; 
Trigger.ADC.InTime=ADCInTime; Trigger.ADC.OutTime=ADCOutTime;
Trigger.ADC.Delay=ADCDelay;  Trigger.ADC.Period=ADCPeriod;  
Trigger.ADC.Width=ADCWidth;  Trigger.ADC.N=ADCN; 
disp([' ADC      ','  |   ', Trigger.ADC.From,'    |', Trigger.ADC.To,'          |   ',num2str(ADCOn),'    |  '...
       num2str(ADCDelay),'   |    ',num2str(ADCPeriod),'     |    ',num2str(ADCN),'     |  ', num2str(ADCWidth)]); 







   
  xmin=min([BurstTimeWindow(1),LaserTimeWindow(1),IITimeWindow(1),CMOSTimeWindow(1)])-round(PockelsPeriod);
  xmin=xmin-PockelsFirstTime;
  xmax=max([BurstTimeWindow(2),LaserTimeWindow(2),IITimeWindow(2),CMOSTimeWindow(2)])+round(PockelsPeriod);
  xmax=xmax-PockelsFirstTime;
  ymin=-0.1; ymax=1.1; 
  

if PlotOn==2
  PlotN=8;  
  figure; %hold on; 
  
  subplot(PlotN,1,1); 
          plot(ADC(:,1)-PockelsFirstTime,ADC(:,2),'b','Linewidth',2);  
          axis([-10000 xmax ymin ymax]);  ylabel('ADC'); 
          title('Fast channels started by Burst');
  subplot(PlotN,1,2);    
          if PockelsOn
          Flash=[[xmin,Flash(1,2)];Flash;[xmax,Flash(1,end)];];    
          plot(Flash(:,1)-PockelsFirstTime,Flash(:,2),'k','Linewidth',2);
          end; 
          axis([-10000 xmax ymin ymax]);  ylabel('Flash'); 
  subplot(PlotN,1,3);    
          if PockelsOn
          Pockels=[[xmin,Pockels(1,2)];Pockels;[xmax,Pockels(1,end)];];                  
          plot(Pockels(:,1)-PockelsFirstTime,Pockels(:,2),'r','Linewidth',2);
          end; 
          axis([-10000 xmax ymin ymax]);  ylabel('Pockels');           
  subplot(PlotN,1,5);    
          if IIOn
          IIGatePlasma=[[xmin,IIGatePlasma(1,2)];IIGatePlasma;[xmax,IIGatePlasma(1,end)];];                                
          plot(IIGatePlasma(:,1)-PockelsFirstTime,IIGatePlasma(:,2),'--c','Linewidth',2);
          end; 
          axis([-10000 xmax ymin ymax]);  ylabel('IIGatePlasma');    
  subplot(PlotN,1,4);    
          if IIOn
          IIGateLaser=[[xmin,IIGateLaser(1,2)];IIGateLaser;[xmax,IIGateLaser(1,end)];];                                
          plot(IIGateLaser(:,1)-PockelsFirstTime,IIGateLaser(:,2),'c','Linewidth',2);
          if FlashBoolOn
             hold on; 
             plot(FlashBool(:,1)-PockelsFirstTime,0.5*FlashBool(:,2),'k','Linewidth',2);
          end; 
          end; 
          axis([-10000 xmax ymin ymax]);  ylabel('IIGateLaser');               
  subplot(PlotN,1,6);    
          if CMOSLaserOn
             CMOSLaser=[[xmin,CMOSLaser(1,2)];CMOSLaser;[xmax,CMOSLaser(1,end)];];                                              
             plot(CMOSLaser(:,1)-PockelsFirstTime,CMOSLaser(:,2),'g','Linewidth',2); 
          end;
          axis([-10000 xmax ymin ymax]);  ylabel('CMOSLaser');                      
  subplot(PlotN,1,7);    
          if CMOSPlasmaOn
             CMOSPlasma=[[xmin,CMOSPlasma(1,2)];CMOSPlasma;[xmax,CMOSPlasma(1,end)];];                                              
             plot(CMOSPlasma(:,1)-PockelsFirstTime,CMOSPlasma(:,2),'--g','Linewidth',2); 
          end;
          axis([-10000 xmax ymin ymax]);  ylabel('CMOSPlasma');                                
          xlabel('t, \mus');
  subplot(PlotN,1,8);    
          %if AUGTriggerOn==1
             Burst=[[xmin,Burst(1,2)];Burst;[xmax,Burst(1,end)];];                                              
             plot(Burst(:,1),Burst(:,2),'--k','Linewidth',2); 
          %end;
          axis([-10000 xmax ymin ymax]);  ylabel('Burst');                                
          xlabel('t, \mus');
end;

if PlotOn
    
figure; hold on; 
plot(ADC(:,1)-PockelsFirstTime,ADC(:,2),'b','Linewidth',2);  
plot(Flash(:,1)-PockelsFirstTime,1.2*Flash(:,2),'k','Linewidth',2);
plot(Pockels(:,1)-PockelsFirstTime,1.2*Pockels(:,2),'r','Linewidth',2);
plot(IIGateLaser(:,1)-PockelsFirstTime,IIGateLaser(:,2),'c','Linewidth',2);
plot(IIGatePlasma(:,1)-PockelsFirstTime,0.8*IIGatePlasma(:,2),'--c','Linewidth',2);
plot(CMOSLaser(:,1)-PockelsFirstTime,1.1*0.6*CMOSLaser(:,2),'g','Linewidth',2); 
plot(CMOSPlasma(:,1)-PockelsFirstTime,0.4*CMOSPlasma(:,2),'--g','Linewidth',2); 
plot(Burst(:,1)-PockelsFirstTime,0.3*Burst(:,2),'--k','Linewidth',2);
   axis([xmin xmax 0,1.4]); xlabel('t, \mus');
legend('ADC','Flash','Pockels','IIGateLaser','IIGatePlasma','CMOSLaser','CMOSPlasma','Burst' );    
end; 



  

