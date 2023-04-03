def calc_expected_power(df_in, gpoa_col, vmpp, impp, gamma, tmod_col=None,
              number_of_strings=1, modules_per_string=1,
              temp_corr=False):
    # installed Capacity in kW
    installed_capacity = (impp * vmpp * number_of_strings * modules_per_string)/1000
    expected_power = df_in[gpoa_col] * installed_capacity

    # apply temperature correction
    if temp_corr:
        gamma = float(gamma)/100
        expected_power = expected_power * (1 + gamma * (df_in[tmod_col] - 25))

    return expected_power

