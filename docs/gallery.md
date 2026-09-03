# Gallery

## BVH Debug

The image below will be used as the reference image for the BVH debug images.

<div id="bvhDebugCombinedViewer">
    <img id="bvhDebugCombinedImage" src="../assets/gallery/BVH_Debug/combined_16384.png">
</div>

### BVH Bounds

#### Layer

<div id="bvhBoundsLayerViewer">
    <img id="bvhBoundsLayerImage" src="../assets/gallery/BVH_Debug/Bounds/Layer/layer_all.png">
</div>

<p id="bvhBoundsLayerLabel" style="font-weight:600; margin-top: 4px;">Layer: All</p>

<input type="range" id="bvhBoundsLayerSlider" min="-1" max="28" step="1" value="-1">

<script>
    const bvhBoundsLayerSlider = document.getElementById("bvhBoundsLayerSlider");
    const bvhBoundsLayerImage = document.getElementById("bvhBoundsLayerImage");
    const bvhBoundsLayerLabel = document.getElementById("bvhBoundsLayerLabel");

    bvhBoundsLayerSlider.addEventListener("input", function() {
        const layer = bvhBoundsLayerSlider.value;

        if (layer == -1) {
            bvhBoundsLayerImage.src = "../assets/gallery/BVH_Debug/Bounds/Layer/layer_all.png";
            bvhBoundsLayerLabel.textContent = "Layer: All";
        } else {
            bvhBoundsLayerImage.src = "../assets/gallery/BVH_Debug/Bounds/Layer/layer_" + layer + ".png";
            bvhBoundsLayerLabel.textContent = "Layer: " + layer;
        }
    });
</script>

#### Depth

<div id="bvhBoundsDepthViewer">
    <img id="bvhBoundsDepthImage" src="../assets/gallery/BVH_Debug/Bounds/Depth/depth_max.png">
</div>

<p id="bvhBoundsDepthLabel" style="font-weight:600; margin-top: 4px;">Depth: Max</p>

<input type="range" id="bvhBoundsDepthSlider" min="-1" max="28" step="1" value="-1">

<script>
    const bvhBoundsDepthSlider = document.getElementById("bvhBoundsDepthSlider");
    const bvhBoundsDepthImage = document.getElementById("bvhBoundsDepthImage");
    const bvhBoundsDepthLabel = document.getElementById("bvhBoundsDepthLabel");

    bvhBoundsDepthSlider.addEventListener("input", function() {
        const depth = bvhBoundsDepthSlider.value;

        if (depth == -1) {
            bvhBoundsDepthImage.src = "../assets/gallery/BVH_Debug/Bounds/Depth/depth_max.png";
            bvhBoundsDepthLabel.textContent = "Depth: All";
        } else {
            bvhBoundsDepthImage.src = "../assets/gallery/BVH_Debug/Bounds/Depth/depth_" + depth + ".png";
            bvhBoundsDepthLabel.textContent = "Depth: " + depth;
        }
    });
</script>

### BVH Depth

<div id="bvhDepthViewer">
    <img id="bvhDepthImage" src="../assets/gallery/BVH_Debug/Depth/depth.png">
</div>

### Disintegration

Now, what happens when the path tracer breaks out the BVH traversal after a certain maximum depth? Use the slider below to find out.

<div id="bvhDisintegrationViewer">
    <img id="bvhDisintegrationImage" src="../assets/gallery/BVH_Debug/Disintegration/depth_32.png">
</div>

<p id="bvhDisintegrationLabel" style="font-weight:600; margin-top: 4px;">Depth: Max</p>

<input type="range" id="bvhDisintegrationSlider" min="0" max="5" step="1" value="0">
<span id="sliderValue">32</span>

<script>
    const bvhDisintegrationSlider = document.getElementById("bvhDisintegrationSlider");
    const bvhDisintegrationImage = document.getElementById("bvhDisintegrationImage");
    const bvhDisintegrationLabel = document.getElementById("bvhDisintegrationLabel");
    const sliderValueDisplay = document.getElementById("sliderValue");

    const depthSteps = [32, 16, 8, 4, 2, 1];

    bvhDisintegrationSlider.addEventListener("input", function() {
        const index = bvhDisintegrationSlider.value;
        const depth = depthSteps[index];

        bvhDisintegrationImage.src = "../assets/gallery/BVH_Debug/Disintegration/depth_" + depth + ".png";
        sliderValueDisplay.textContent = depth;
    });
</script>
