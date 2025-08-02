# Bartlett-Lewis Model for Stochastic Rainfall Disaggregation
--------------------------------------------------------------

This model implements the stochastic logic of the Bartlett-Lewis process to simulate the temporal structure of precipitation and perform the disaggregation of coarse temporal resolution rainfall series (such as daily or hourly) into finer series (such as 10 minutes).

Model Parameters (calibrated based on a high-resolution rainfall series):
- lambda (λ): average frequency of storm occurrences (rain events) per day.
- beta (β): average number of pulses (small rain events) per storm.
- gamma (γ): termination rate of the storm (inverse of the average duration of the rain event).
- eta (η): termination rate of a pulse (inverse of the average duration of the rain pulse).
- mu (μ): average rainfall intensity per pulse (mm).

Usage Flow:
-------------
1. **Model Calibration**
    - Load the fine resolution rainfall series with a fixed interval (e.g., 10 minutes).
    - Identify rain events based on a minimum dry period between them (inter_event_gap).
    - Calibrate the model parameters based on the statistics of these events.

2. **Disaggregation**
    - Load the coarse resolution rainfall series (e.g., hourly).
    - For each observed value in the coarse series:
        - Simulate a rain event based on the calibrated parameters.
        - Adjust the simulated rainfall intensity to match the observed volume.
        - Divide the simulated rainfall into the desired finer intervals.

3. **Export and Validation**
    - Export the calibrated parameters in YAML format for reuse.
    - Compare the disaggregated series with real data visually and statistically (when available).

Observations:
------------
- The parameter calibration uses the Method of Moments (MoM), which is simpler than MLE but more straightforward.
- The disaggregation is stochastic: each execution may generate a different distribution for the same input value.
- It is recommended to use a random seed to ensure reproducibility of the results.
- The model is suitable for hydrological applications where the temporal distribution of rainfall affects runoff, infiltration, among other processes.

Example of Calibrated Parameters:
---------------------------------
lambda: 17.5        # ~17 rain events per day  
beta: 5.0           # ~5 pulses per event  
gamma: 0.05         # ~20 minutes duration per event  
eta: 0.1            # ~10 minutes per pulse  
mu: 0.12            # ~0.12 mm per rain pulse