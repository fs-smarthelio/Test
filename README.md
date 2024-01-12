# Utils
This includes two main functions from which one is used to manipulate the dataframe and add one more level in dataframe columns, and second one 
is used to filter the data from the dataframe considering how much tolerated data you want, and here you'll also get the flexibility to decide the tolerance level
and also which data you want:
1. Data, which is having the tolerance value above the threshold.
2. Or the data is having value below than that threshold.
## Functions
* **add_index_curve_level(df, curve):**
Add a new index level to the dataframe converting it into a multi-index dataframe and swap the levels accordingly.

    *Parameters:*
  1. df(pd.DataFrame): The DataFrame whose columns need to be adjusted.
  2. curve (str): The name of the level to be used to create the new level.
  
  *Returns:* 
  * pd.DataFrame: DataFrame with adjusted multi-index columns.
  * <img src="C:\Users\frank\OneDrive\Desktop\Capture.PNG"/>
      

* **column_pattern_filter(df, sensitivity=0.1, good_filter_data=True)**
Filter DataFrame based on deviations between specified columns.

    *Parameters:*
   1. df(pd.DataFrame): Input DataFrame containing columns for comparison.
   2. sensitivity (float, optional): Tolerance level for deviation filtering (default is 0.1).
   3. good_filter_data (bool, optional):![Untitled-2023-12-04-1606](https://github.com/fs-smarthelio/test/assets/143487427/e3555216-4aa8-4996-b0dc-927b594dd3da)

       * If TRUE, retains data within the sensitivity tolerance.
       * If FALSE, retains data exceeding the sensitivity tolerance (default is True).
    
   *Returns:*
    * pd.DataFrame: Filtered DataFrame based on specified deviations and tolerance.
