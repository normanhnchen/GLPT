# Probability Density Functions (PDF)

A PDF is a function that describes the likelyhood a random sampled value is going to take on a certain value. This is important in computer graphics, especially in sampling techniques, as using a PDF can mimick the behaviour of light in real life, reduce noise, and increase rendering speed. However, since it creates bias for certain values (which increases density of samples in important areas), we must divide by its PDF value (rate of probability) to guarantee an unbiased result.

Source: https://www.scratchapixel.com/lessons/mathematics-physics-for-computer-graphics/monte-carlo-methods-mathematical-foundations/quick-introduction-to-monte-carlo-methods.html
