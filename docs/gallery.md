# Gallery

## BVH Debug

The image below will be used as the reference image for the BVH debug images.

<style>
    .gallery-card {
        border: 2px solid var(--md-default-fg-color--lightest);
        border-radius: 8px;
        padding: 16px;
        margin: 24px 0;
    }

    .gallery-viewer {
        max-width: 600px;
        margin: 0 auto;
    }

    .gallery-viewer img {
        width: 100%;
        border-radius: 6px;
    }

    .gallery-label {
        text-align: center;
        font-weight: 600;
        margin: 8px 0;
    }

    .gallery-credit {
        text-align: left;
        font-size: 14px;
    }

    input[type="range"] {
        width: 100%;
        margin: 0 auto;
        accent-color: var(--md-primary-fg-color);
    }
</style>

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="bvhDebugCombinedImage" src="../assets/gallery/BVH_Debug/combined_16384.png">
    </div>
    <p class="gallery-credit">BMW car model courtesy of Mike Pan and Morgan McGuire, license CC0/Public Domain. (Model downloaded from Morgan McGuire's Computer Graphics Archive https://casual-effects.com/data.)</p> 
</div>

### BVH Bounds

#### Layer

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="bvhBoundsLayerImage" src="../assets/gallery/BVH_Debug/Bounds/Layer/layer_all.png">
    </div>
    <p class="gallery-credit">BMW car model courtesy of Mike Pan and Morgan McGuire, license CC0/Public Domain. (Model downloaded from Morgan McGuire's Computer Graphics Archive https://casual-effects.com/data.)</p> 
    <p class="gallery-label" id="bvhBoundsLayerLabel">Layer: All</p>
    <input type="range" id="bvhBoundsLayerSlider" min="-1" max="28" step="1" value="-1">
</div>

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

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="bvhBoundsDepthImage" src="../assets/gallery/BVH_Debug/Bounds/Depth/depth_max.png">
    </div>
    <p class="gallery-credit">BMW car model courtesy of Mike Pan and Morgan McGuire, license CC0/Public Domain. (Model downloaded from Morgan McGuire's Computer Graphics Archive https://casual-effects.com/data.)</p> 
    <p class="gallery-label" id="bvhBoundsDepthLabel">Depth: Max</p>
    <input type="range" id="bvhBoundsDepthSlider" min="-1" max="28" step="1" value="-1">
</div>

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

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="bvhDepthImage" src="../assets/gallery/BVH_Debug/Depth/depth.png">
    </div>
    <p class="gallery-credit">BMW car model courtesy of Mike Pan and Morgan McGuire, license CC0/Public Domain. (Model downloaded from Morgan McGuire's Computer Graphics Archive https://casual-effects.com/data.)</p> 
</div>

### Disintegration

Now, what happens when the path tracer breaks out the BVH traversal after a certain maximum depth? Use the slider below to find out.

<div class="gallery-card">
    <div class="gallery-viewer">
        <img id="bvhDisintegrationImage" src="../assets/gallery/BVH_Debug/Disintegration/depth_32.png">
    </div>
    <p class="gallery-credit">BMW car model courtesy of Mike Pan and Morgan McGuire, license CC0/Public Domain. (Model downloaded from Morgan McGuire's Computer Graphics Archive https://casual-effects.com/data.)</p> 
    <p class="gallery-label" id="bvhDisintegrationLabel">Max Depth: 32</p>
    <div class="gallery-slider-row">
        <input type="range" id="bvhDisintegrationSlider" min="0" max="5" step="1" value="0">
        <span id="bvhDisintegrationSliderValue">32</span>
    </div>
</div>

<script>
    const bvhDisintegrationSlider = document.getElementById("bvhDisintegrationSlider");
    const bvhDisintegrationImage = document.getElementById("bvhDisintegrationImage");
    const bvhDisintegrationLabel = document.getElementById("bvhDisintegrationLabel");
    const sliderValueDisplay = document.getElementById("bvhDisintegrationSliderValue");

    const depthSteps = [32, 16, 8, 4, 2, 1];

    bvhDisintegrationSlider.addEventListener("input", function() {
        const index = bvhDisintegrationSlider.value;
        const depth = depthSteps[index];

        bvhDisintegrationImage.src = "../assets/gallery/BVH_Debug/Disintegration/depth_" + depth + ".png";
        bvhDisintegrationLabel.textContent = "Max Depth: " + depth;
        sliderValueDisplay.textContent = depth;
    });
</script>
