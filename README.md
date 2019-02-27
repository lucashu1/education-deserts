# Education Deserts Project:

By: Lucas Hu, Nikhil Sinha, Chengyi (Jeff) Chen, Ashwath Raj

---
## Problem Statement
The social issue we are addressing is education. Specifically, we are addressing the limited accessibility of higher education in specific pockets of the United States. These areas of limited accessibility are called education deserts because they are areas that do not contain any colleges within sixty miles, or any similar distance that limits a student’s ability to attend college. In the American Council of Education’s report on "Education Deserts: The Continued Significance of “Place” in the Twenty-First Century” they state that “the majority —57.4 percent—of incoming freshmen attending public four-year colleges enroll within 50 miles from their permanent home” (ACE). Given the fact that millions of adult and student Americans live in these education deserts, it’s easy to see the effect that geographical limitations can have on higher poverty rates and below average income. 

Our project seeks to help alleviate the issue of geographically limited college accessibility by mapping where education deserts are. Then, by calculating the potential socioeconomic impact of placing colleges in those areas, we can create a framework for optimizing the benefits of building new colleges in any given education desert. 

---
## Project Components
Our project will be divided into 3 primary steps:

### Data Mining: 
First, we will look at the locations of existing colleges to discover regions in the U.S. that are currently “education deserts.” We will define an “education desert” as a region in that does not have any colleges within a 50-minute commute. This is essentially the first step in our project, and should be the first component we complete.

We will then use census data to discover which features of a region are predictive of that region being an education desert. This will be accomplished by training a binary classifier to identify regions as being education deserts or not, and then interpreting the feature importances of that classifier.


### Prediction: 
Next, want to predict the “population cover” of existing colleges in the U.S. (i.e. how many college graduates each college contributes to the region). We will do this by looking at non-education desert regions in particular, and using census data to regress on the percentage of the population in that region that have college degrees. (For the time being, we can progress on this in parallel with step 1, by ignoring whether or not a given region is labeled as an education desert.)

By applying this regressor to regions that are currently education deserts, we will be able to predict the economic impact of a hypothetical new college (by way of increased college graduate salaries), if a new college were to be built within (or near) a current education desert region.


### Optimization: 
Lastly, we will use the findings from Step 2 to decide where to create new colleges in the U.S. so as to maximize the overall increase in economic impact. Let’s say we have the budget to create 10 new colleges: where should we place those 10 colleges so as to maximize the increase in total college graduate salaries? (Algorithm to be described more in Section 4.)

This will be the last step in our project. If we want to work in parallel, we can start off by optimizing for alternative/proxy metrics, so that we can have the overall optimization pipeline ready to go before Step 2 is complete.

---
## Datasets
We will be primarily working with 3 data sources: the American Community Survey 5-Year Estimates in Census Block Groups dataset that contains 220,334 rows for each census block group and 2161 columns for each feature like Median Earnings broken down by education level, as well as Age and Occupation data; shape files for each state that include the latitude and longitude coordinates of the polygons that describe a specific census block group; and the Integrated Post-secondary Education Data System dataset which contains a list of 1534 colleges and 145 features about each school, including the exact location of the school. 

### Data Mining: 
We will first loop through all the census block groups, represented as polygons, and calculate the latitude / longitude position of it’s centroid. Subsequently, we would either 
1. Loop through the list of colleges and use the Haversine formula to calculate the  map distance between each college and each census block group, labelling any census-block group that is not within a 50 mile radius to the school as an Education Desert [0] and whichever is within distance as a Non-education Desert [1], 
OR 
2. Use tries to find the longest matching suffix (lat-long pairs) to compute 1 distance per census block, rather than all (block, uni) pairs, giving us a reduced runtime of O(m+n), rather than O(n^2) as per the former approach.

### Prediction: 
One of the major features we will use in order to figure out the economic impact of the education desert would be to use the columns from the ACS dataset: 
`Population 25 Years and Over: Some College or More`, 
`Occupied Housing Units`,
`Median Earnings: <Gender><Education Level>`.

---
## Approaches/Metrics
For the different parts of our project, we will employ different techniques to try to generate the best results.

### Data mining: 
After calculating the distances between the colleges and the census blocks, whether using the trie technique or the pair distance technique, we will train a Support Vector Machine classifier to try and differentiate between education deserts (1) and non-education deserts (0). While the predictions of this classifier will tell us information that we already know, doing a feature importance analysis will tell us what the most important features or feature pairs will be to determining whether an area is in an education desert or not. This can inform us of things to focus on later on in the project. The reason we will use an SVM classifier is due to the SVM’s affinity for drawing decision boundaries for non-linear functions, or essentially its ability to do binary classification.


### Population cover estimation: 
The way that we will approach this task is relatively complex. First, we will compute the ratio between the number of people with college degrees and the number of people who are of working age for every given census block group. These numbers will be used by our model as labels that determine the percentage of people who go to college in any given region. From here, we will train a standard feed-forward neural network using the rest of the census features to try and predict the value of this percentage. However, to train this model, we will decrease the amount of data that we are using to only include the areas which are not in education deserts. The reason for this is because we want to estimate that if we were to put a college in another region that is an education desert, what percentage of the population in the surrounding communities would go to college. This allows us to generate a more precise estimate of how many new students would attend college if we were to put them in any specific education desert.


### Optimization: 
We will approach this optimization problem in two ways: with and without the population cover estimation. Without the population cover estimation, we will try to maximize the number of students that have access to a college education. This will mean trying to place a college in every census block group and computing how many new people will have access to college, and recording the top k locations by number of new people with collegiate accessibility. With the population cover estimation, we will try to maximize the economic benefit for every college that we could theoretically place. To do this, we would place the college in any census block and determine which census blocks would be covered by the 50 mile constraint. We would then calculate the population cover for each of these census block groups and then compute the difference between the current percentage of people who go to college in the region and our estimate. This will tell us the percentage of people who would have a college education if there were a college in the region but do not currently. From here we assume that the average salary of these new college graduates will be the average salary of a college graduate. We then calculate a new average salary for the region using this figure. Multiplying the new average salary by the working population of the region gives us a total salary estimate. We repeat the same calculation using the original average salary and subtract these two values to get a figure that tells us the number of dollars added by the college to the surrounding population. We compute this value for every potential census block group and record the top k values. This leaves us with two sets of recommendations for where to place new colleges to maximize different objectives.