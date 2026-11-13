import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  CalendarDays,
  Check,
  Heart,
  LayoutDashboard,
  LoaderCircle,
  Shirt,
  ShoppingBag,
  Search,
  Sparkles,
  Trash2,
  Upload
} from "lucide-react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const CATEGORIES = [
  "Dresses", "Jackets", "Jeans", "Kurtas", "Shirts",
  "Shorts", "Skirts", "Tops", "Trousers", "Tshirts"
];
const MODEL_RESULTS = [
  {
    name: "VGG16",
    accuracy: 84.3,
    loss: 0.4507,
    parameters: 14848586,
    architecture: "ImageNet VGG16 backbone with transfer learning and a fashion classification head."
  },
  {
    name: "Custom CNN",
    accuracy: 88.44,
    loss: 0.3525,
    parameters: 13236298,
    architecture: "Task-specific convolutional network trained on the ten catalogue categories."
  },
  {
    name: "ResNet50",
    accuracy: 90.51,
    loss: 0.2721,
    parameters: 24114826,
    architecture: "Residual ImageNet ResNet50 backbone with skip connections and a classification head."
  }
];

const MENU = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "AI Fitting Room", icon: Shirt },
  { name: "Identify Clothing", icon: Upload },
  { name: "OOTD Stylist", icon: Sparkles },
  { name: "Explore Clothes", icon: ShoppingBag },
  { name: "Model Performance", icon: BarChart3 },
  { name: "My Wardrobe", icon: Heart },
  { name: "Compatibility Checker", icon: Check },
  { name: "Smart Fashion Search", icon: Search },
  { name: "Weekly Planner", icon: CalendarDays },
  { name: "Fashion Intelligence", icon: BarChart3 }
];
const COLOUR_WORDS = ["black", "white", "grey", "gray", "blue", "navy", "red", "green", "yellow", "pink", "brown", "beige", "orange", "purple"];
const VTON_SAMPLE_CLOTHES = ["01260_00.jpg", "01430_00.jpg", "02783_00.jpg"];
const VTON_SAMPLE_PEOPLE = ["00891_00.jpg", "03615_00.jpg", "07445_00.jpg"];
const STARTER_WARDROBE = [
  { id: "starter-red-knit", name: "Red Knit Top", category: "Tops", colour: "red", image: `${API_BASE}/vton-examples/cloth/01260_00.jpg` },
  { id: "starter-blue-shirt", name: "Blue Casual Shirt", category: "Shirts", colour: "blue", image: `${API_BASE}/vton-examples/cloth/01430_00.jpg` },
  { id: "starter-black-top", name: "Black Essential Top", category: "Tops", colour: "black", image: `${API_BASE}/vton-examples/cloth/02783_00.jpg` },
  { id: "starter-white-shirt", name: "White Everyday Shirt", category: "Shirts", colour: "white", image: `${API_BASE}/vton-examples/cloth/03751_00.jpg` },
  { id: "starter-green-top", name: "Green Relaxed Top", category: "Tops", colour: "green", image: `${API_BASE}/vton-examples/cloth/06802_00.jpg` },
  { id: "starter-neutral-layer", name: "Neutral Layered Top", category: "Tops", colour: "neutral", image: `${API_BASE}/vton-examples/cloth/09933_00.jpg` },
];
function extractColour(name) {
  const lowerName = name.toLowerCase();
  return COLOUR_WORDS.find((colour) => lowerName.includes(colour)) || "neutral";
}

function ProductImage({ product, className = "", ...props }) {
  return (
    <img
      className={className}
      src={`${API_BASE}${product.image}`}
      alt={product.name}
      loading="lazy"
      {...props}
    />
  );
}

function App() {
  const [page, setPage] = useState("Dashboard");
  const [products, setProducts] = useState([]);
  const [allProducts, setAllProducts] = useState([]);
  const [catalogueTotal, setCatalogueTotal] = useState(0);
  const [catalogueLoading, setCatalogueLoading] = useState(true);
  const [catalogueError, setCatalogueError] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [catalogueSearch, setCatalogueSearch] = useState("");
  const [catalogueSort, setCatalogueSort] = useState("default");
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [image, setImage] = useState(null);
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionError, setActionError] = useState("");
  const [wardrobe, setWardrobe] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem("vestiar-wardrobe") || "[]");
      const savedIds = new Set(saved.map((item) => item.id));
      return [...saved, ...STARTER_WARDROBE.filter((item) => !savedIds.has(item.id))];
    } catch {
      return STARTER_WARDROBE;
    }
  });
  const [wardrobeName, setWardrobeName] = useState("");
  const [wardrobeCategory, setWardrobeCategory] = useState(CATEGORIES[0]);
  const [wardrobeImage, setWardrobeImage] = useState("");
  const [wardrobeSearch, setWardrobeSearch] = useState("");
  const [wardrobeCategoryFilter, setWardrobeCategoryFilter] = useState("All");
  const [wardrobeFavorites, setWardrobeFavorites] = useState(() => {
    try { return JSON.parse(localStorage.getItem("vestiar-wardrobe-favourites") || "[]"); } catch { return []; }
  });
  const [occasion, setOccasion] = useState("Casual");
  const [weather, setWeather] = useState("Any");
  const [style, setStyle] = useState("Minimal");
  const [clothingPreference, setClothingPreference] = useState("Any");
  const [outfit, setOutfit] = useState(null);
  const [outfitRecommendations, setOutfitRecommendations] = useState([]);
  const [savedOutfits, setSavedOutfits] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem("vestiar-outfits") || "[]");
      return Array.isArray(saved) ? saved : [];
    } catch {
      return [];
    }
  });
  const [personFile, setPersonFile] = useState(null);
  const [personImage, setPersonImage] = useState(null);
  const [personDimensions, setPersonDimensions] = useState(null);
  const [garmentFile, setGarmentFile] = useState(null);
  const [garmentImage, setGarmentImage] = useState(null);
  const [garmentDimensions, setGarmentDimensions] = useState(null);
  const [garmentCategory, setGarmentCategory] = useState("upper_body");
  const [tryOnResult, setTryOnResult] = useState(null);
  const [tryOnLoading, setTryOnLoading] = useState(false);
  const [tryOnError, setTryOnError] = useState("");
  const [tryOnStage, setTryOnStage] = useState("");
  const [showTryOnComparison, setShowTryOnComparison] = useState(false);
  const [savedTryOns, setSavedTryOns] = useState(() => {
    try { return JSON.parse(localStorage.getItem("vestiar-saved-tryons") || "[]"); } catch { return []; }
  });
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(localStorage.getItem("vestiar-history") || "[]"); } catch { return []; }
  });
  const [compatibilityItems, setCompatibilityItems] = useState([]);
  const [compatibilityResult, setCompatibilityResult] = useState(null);
  const [searchPreview, setSearchPreview] = useState(null);
  const [similarProducts, setSimilarProducts] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [weeklyPlan, setWeeklyPlan] = useState(() => {
    try { return JSON.parse(localStorage.getItem("vestiar-weekly-plan") || "{}"); } catch { return {}; }
  });

  useEffect(() => {
    let active = true;
    const loadCatalogue = async () => {
      setCatalogueLoading(true);
      setCatalogueError("");
      try {
        const response = await fetch(`${API_BASE}/api/catalogue?category=${encodeURIComponent(selectedCategory)}&limit=100`);
        if (!response.ok) throw new Error("Catalogue request failed");
        const data = await response.json();
        if (active) {
          setProducts(data.products || []);
          setCatalogueTotal(data.total || data.products?.length || 0);
          if (selectedCategory === "All") setAllProducts(data.products || []);
        }
      } catch {
        if (active) setCatalogueError("The catalogue could not be loaded. Start the backend and try again.");
      } finally {
        if (active) setCatalogueLoading(false);
      }
    };
    loadCatalogue();
    return () => { active = false; };
  }, [selectedCategory]);

  useEffect(() => {
    localStorage.setItem("vestiar-wardrobe", JSON.stringify(wardrobe));
  }, [wardrobe]);

  useEffect(() => {
    localStorage.setItem("vestiar-outfits", JSON.stringify(savedOutfits));
  }, [savedOutfits]);
  useEffect(() => {
    localStorage.setItem("vestiar-wardrobe-favourites", JSON.stringify(wardrobeFavorites));
    localStorage.setItem("vestiar-history", JSON.stringify(history));
    localStorage.setItem("vestiar-weekly-plan", JSON.stringify(weeklyPlan));
  }, [wardrobeFavorites, history, weeklyPlan]);

  useEffect(() => {
    localStorage.setItem("vestiar-saved-tryons", JSON.stringify(savedTryOns));
  }, [savedTryOns]);

  const featuredProducts = useMemo(() => products.slice(0, 4), [products]);

  const selectPage = (nextPage) => {
    setPage(nextPage);
    setActionError("");
  };

  const readImageFile = (file, label, onReady) => {
    if (!file || !["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setTryOnError(`Please choose a JPG, JPEG or WEBP ${label} image.`);
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setTryOnError(`The ${label} image must be smaller than 10 MB.`);
      return;
    }
    const preview = URL.createObjectURL(file);
    const imageElement = new Image();
    imageElement.onload = () => {
      URL.revokeObjectURL(preview);
      const width = imageElement.naturalWidth;
      const height = imageElement.naturalHeight;
      const minimumDimension = label === "person" ? 256 : 32;
      if (width < minimumDimension || height < minimumDimension) {
        setTryOnError(`The ${label} image is ${width}x${height}px. It must be at least ${minimumDimension}x${minimumDimension}px.`);
        return;
      }
      onReady(file, URL.createObjectURL(file), { width, height });
    };
    imageElement.onerror = () => {
      URL.revokeObjectURL(preview);
      setTryOnError("The selected file is not a readable image.");
    };
    imageElement.src = preview;
  };

  const handlePersonImage = (event) => {
    const selected = event.target.files?.[0];
    readImageFile(selected, "person", (file, preview, dimensions) => {
      if (personImage) URL.revokeObjectURL(personImage);
      setPersonFile(file);
      setPersonImage(preview);
      setPersonDimensions(dimensions);
      setTryOnResult(null);
      setShowTryOnComparison(false);
      setTryOnError("");
    });
  };

  const handleGarmentImage = (event) => {
    const selected = event.target.files?.[0];
    readImageFile(selected, "garment", (file, preview, dimensions) => {
      if (garmentImage) URL.revokeObjectURL(garmentImage);
      setSelectedProduct(null);
      setGarmentFile(file);
      setGarmentImage(preview);
      setGarmentDimensions(dimensions);
      setTryOnResult(null);
      setShowTryOnComparison(false);
      setTryOnError("");
    });
  };

  const chooseSampleImage = async (type, filename) => {
    try {
      const response = await fetch(`${API_BASE}/vton-examples/${type}/${filename}`);
      if (!response.ok) throw new Error("The sample image could not be loaded.");
      const blob = await response.blob();
      const file = new File([blob], filename, { type: blob.type || "image/jpeg" });
      readImageFile(file, type === "image" ? "person" : "garment", (readyFile, preview, dimensions) => {
        if (type === "image") {
          if (personImage) URL.revokeObjectURL(personImage);
          setPersonFile(readyFile);
          setPersonImage(preview);
          setPersonDimensions(dimensions);
        } else {
          if (garmentImage) URL.revokeObjectURL(garmentImage);
          setSelectedProduct(null);
          setGarmentFile(readyFile);
          setGarmentImage(preview);
          setGarmentDimensions(dimensions);
        }
        setTryOnResult(null);
        setShowTryOnComparison(false);
        setTryOnError("");
      });
    } catch (error) {
      setTryOnError(error.message || "The sample image could not be loaded.");
    }
  };

  const generateTryOn = async () => {
    if (!personFile || (!selectedProduct && !garmentFile)) {
      setTryOnError("Provide a person image and select or upload a garment first.");
      return;
    }
    setTryOnLoading(true);
    setTryOnError("");
    setTryOnStage("Uploading images");
    const stages = [
      "Uploading images",
      "Resizing garment",
      "Generating garment mask",
      "Processing human image",
      "Extracting pose and parsing",
      "Synthesizing fitting result",
    ];
    let stageIndex = 0;
    const stageTimer = window.setInterval(() => {
      stageIndex = Math.min(stageIndex + 1, stages.length - 1);
      setTryOnStage(stages[stageIndex]);
    }, 3500);
    const controller = new AbortController();
    const requestTimer = window.setTimeout(() => controller.abort(), 330000);
    try {
      let garment = garmentFile;
      if (!garment && selectedProduct) {
        const garmentResponse = await fetch(`${API_BASE}${selectedProduct.image}`);
        if (!garmentResponse.ok) throw new Error("The selected garment image could not be loaded.");
        const garmentBlob = await garmentResponse.blob();
        garment = new File([garmentBlob], "catalogue-garment.jpg", { type: garmentBlob.type || "image/jpeg" });
      }
      const formData = new FormData();
      formData.append("person_image", personFile);
      formData.append("garment_image", garment);
      formData.append("category", garmentCategory);
      const response = await fetch(`${API_BASE}/api/virtual-tryon`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "AI Fitting Room is unavailable.");
      setTryOnResult(data);
    } catch (error) {
      setTryOnError(error.name === "AbortError" ? "AI Fitting Room timed out after five minutes. Your uploaded images are still available." : error.message || "AI Fitting Room processing failed.");
    } finally {
      window.clearInterval(stageTimer);
      window.clearTimeout(requestTimer);
      setTryOnLoading(false);
      setTryOnStage("");
    }
  };

  const selectCatalogueGarment = (product) => {
    setSelectedProduct(product);
    setGarmentFile(null);
    if (garmentImage) URL.revokeObjectURL(garmentImage);
    setGarmentImage(null);
    setTryOnResult(null);
    setTryOnError("");
  };

  const saveTryOnResult = () => {
    if (!tryOnResult?.generated_image_data) return;
    const item = {
      id: crypto.randomUUID(),
      image: tryOnResult.generated_image_data,
      garment: selectedProduct?.name || "Uploaded garment",
      category: garmentCategory,
      createdAt: new Date().toISOString(),
    };
    setSavedTryOns((items) => [item, ...items]);
    setWardrobe((items) => [{
      id: crypto.randomUUID(),
      name: `Try-on · ${item.garment}`,
      category: selectedProduct?.category || (garmentCategory === "full_body" ? "Dresses" : garmentCategory === "lower_body" ? "Trousers" : "Tops"),
      image: item.image,
    }, ...items]);
  };

  const handleImage = (event) => {
    const selected = event.target.files?.[0];
    if (!selected) return;
    if (!selected.type.startsWith("image/")) {
      setActionError("Please choose an image file.");
      return;
    }
    if (image) URL.revokeObjectURL(image);
    setFile(selected);
    setImage(URL.createObjectURL(selected));
    setResult(null);
    setComparison(null);
    setActionError("");
  };

  const classifyImage = async (compare = false) => {
    if (!file) return;
    setLoading(true);
    setActionError("");
    if (compare) setComparison(null);
    else setResult(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await fetch(`${API_BASE}/api/${compare ? "compare-models" : "classify"}`, {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Request failed");
      if (compare) setComparison(data.model_comparison);
      else {
        setResult(data);
        setHistory((items) => [{
          id: crypto.randomUUID(),
          category: data.category,
          confidence: data.confidence,
          createdAt: new Date().toISOString(),
        }, ...items].slice(0, 50));
      }
    } catch (error) {
      setActionError(error.message || "The backend request failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleWardrobeImage = (event) => {
    const selected = event.target.files?.[0];
    if (!selected || !selected.type.startsWith("image/")) {
      setActionError("Please choose an image file.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => setWardrobeImage(String(reader.result));
    reader.readAsDataURL(selected);
    const formData = new FormData();
    formData.append("file", selected);
    fetch(`${API_BASE}/api/classify`, { method: "POST", body: formData })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Classification failed");
        setWardrobeCategory(data.category);
      })
      .catch(() => setActionError("Image saved for preview, but automatic classification failed."));
  };

  const addWardrobeItem = (event) => {
    event.preventDefault();
    if (!wardrobeName.trim() || !wardrobeImage) {
      setActionError("Add a name and an image before saving.");
      return;
    }
    setWardrobe((items) => [
      { id: crypto.randomUUID(), name: wardrobeName.trim(), category: wardrobeCategory, colour: extractColour(wardrobeName), image: wardrobeImage },
      ...items
    ]);
    setWardrobeName("");
    setWardrobeImage("");
    setActionError("");
  };

  const toggleWardrobeFavourite = (id) => {
    setWardrobeFavorites((items) => items.includes(id) ? items.filter((item) => item !== id) : [...items, id]);
  };

  const toggleCompatibilityItem = (item) => {
    setCompatibilityItems((items) => items.some((entry) => entry.id === item.id)
      ? items.filter((entry) => entry.id !== item.id)
      : [...items, item]);
  };

  const analyseCompatibility = () => {
    const categories = compatibilityItems.map((item) => item.category);
    const colours = compatibilityItems.map((item) => item.colour || extractColour(item.name));
    const topCount = categories.filter((category) => ["Tops", "Shirts", "Tshirts", "Kurtas", "Dresses"].includes(category)).length;
    const bottomCount = categories.filter((category) => ["Jeans", "Trousers", "Shorts", "Skirts"].includes(category)).length;
    const duplicate = new Set(categories).size !== categories.length;
    const colourConflict = new Set(colours).size === 1 && colours[0] !== "neutral" && colours.length > 1;
    const validBase = topCount <= 1 && bottomCount <= 1 && categories.length > 0;
    setCompatibilityResult({
      tone: validBase && !duplicate && !colourConflict ? "Good foundation" : "Needs editing",
      explanation: duplicate
        ? "You selected duplicate garment roles. Keep one main top or dress and one bottom for a balanced outfit."
        : colourConflict
          ? `Every selected item is marked ${colours[0]}. Add a neutral or contrasting colour for clearer outfit separation.`
        : validBase
          ? "The selected pieces cover complementary garment roles. Add one layer or accessory without repeating the same role."
          : "Try combining one top or dress with one bottom. Layering pieces such as jackets can be added separately.",
    });
  };

  const searchSimilar = async (event) => {
    const selected = event.target.files?.[0];
    if (!selected || !selected.type.startsWith("image/")) {
      setSearchError("Please choose an image file.");
      return;
    }
    setSearchPreview(URL.createObjectURL(selected));
    setSearchLoading(true);
    setSearchError("");
    const formData = new FormData();
    formData.append("file", selected);
    try {
      const response = await fetch(`${API_BASE}/api/search-similar`, { method: "POST", body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Similarity search failed");
      setSimilarProducts(data.products || []);
    } catch (error) {
      setSearchError(error.message);
    } finally {
      setSearchLoading(false);
    }
  };

  const plannerDays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

  const generateOutfit = () => {
    const catalogueProducts = allProducts.length ? allProducts : products;
    const sourceProducts = [...catalogueProducts, ...wardrobe].filter((product, index, items) => (
      items.findIndex((candidate) => candidate.id === product.id || candidate.image === product.image) === index
    ));
    if (sourceProducts.length === 0) {
      setActionError("Load the catalogue before generating an outfit.");
      return;
    }
    const preferenceWords = `${occasion} ${weather} ${style} ${clothingPreference}`.toLowerCase().split(/\s+/);
    const preferredCategories = new Set(
      clothingPreference === "Ethnic"
        ? ["Kurtas", "Dresses"]
        : clothingPreference === "Western"
          ? ["Jeans", "Tshirts", "Tops", "Shirts", "Jackets", "Trousers"]
          : clothingPreference === "Indo-Western"
            ? ["Kurtas", "Tops", "Dresses", "Jackets"]
            : ["Tops", "Shirts", "Tshirts", "Jeans", "Trousers", "Dresses", "Jackets"]
    );
    const occasionCategories = {
      College: ["Tshirts", "Jeans", "Tops", "Shirts"],
      Casual: ["Tops", "Tshirts", "Jeans", "Shorts"],
      Party: ["Dresses", "Tops", "Skirts", "Jackets"],
      Traditional: ["Kurtas", "Dresses", "Skirts"],
      Formal: ["Shirts", "Trousers", "Dresses", "Jackets"],
      Travel: ["Tshirts", "Jeans", "Shorts", "Jackets"],
      "Special events": ["Dresses", "Kurtas", "Tops"],
    };
    const occasionCategorySet = new Set(occasionCategories[occasion] || []);
    const weatherCategories = weather === "Cold" ? new Set(["Jackets", "Trousers", "Jeans", "Dresses"]) : new Set();
    const scoredProducts = sourceProducts
      .map((product) => {
        const searchable = `${product.name} ${product.category}`.toLowerCase();
        const preferenceScore = preferenceWords.reduce((score, word) => score + (word !== "any" && searchable.includes(word) ? 2 : 0), 0);
        const categoryScore = (preferredCategories.has(product.category) ? 5 : 0)
          + (occasionCategorySet.has(product.category) ? 4 : 0)
          + (weatherCategories.has(product.category) ? 2 : 0);
        return { product, score: preferenceScore + categoryScore, tieBreaker: Math.random() };
      })
      .sort((left, right) => right.score - left.score || right.tieBreaker - left.tieBreaker);
    const recommendations = scoredProducts.slice(0, Math.min(10, scoredProducts.length)).map(({ product }) => product);
    const tops = recommendations.filter((item) => ["Tops", "Shirts", "Tshirts", "Kurtas"].includes(item.category));
    const bottoms = recommendations.filter((item) => ["Jeans", "Trousers", "Shorts", "Skirts"].includes(item.category));
    const layers = recommendations.filter((item) => ["Jackets", "Dresses"].includes(item.category));
    const top = tops[0] || recommendations[0];
    const bottom = bottoms[0];
    const layer = ["Cold", "Party", "Formal"].includes(weather) || occasion === "Party" ? layers[0] : null;
    const explanation = `${style} ${clothingPreference.toLowerCase()} styling for a ${occasion.toLowerCase()} setting${weather !== "Any" ? ` in ${weather.toLowerCase()} weather` : ""}.`;
    setOutfitRecommendations(recommendations);
    setOutfit({ top, bottom, layer, explanation });
  };

  const saveOutfit = () => {
    if (!outfit) return;
    setSavedOutfits((items) => [{ id: crypto.randomUUID(), createdAt: new Date().toISOString(), favourite: false, ...outfit }, ...items]);
  };

  const toggleSavedOutfitFavourite = (id) => {
    setSavedOutfits((items) => items.map((item) => item.id === id ? { ...item, favourite: !item.favourite } : item));
  };

  const tryOutfit = () => {
    if (!outfit?.top) return;
    selectCatalogueGarment(outfit.top);
    selectPage("AI Fitting Room");
  };

  const renderDashboard = () => (
    <section className="dashboard">
      <div className="hero">
        <div>
          <p className="eyebrow">WELCOME TO VESTIAR</p>
          <h1>Style that feels like you.</h1>
          <p className="hero-text">Explore your wardrobe, discover new combinations and preview pieces with an AI-assisted fitting space.</p>
          <button className="hero-button" onClick={() => selectPage("AI Fitting Room")}>Start styling <Sparkles size={16} /></button>
        </div>
        <div className="hero-art"><Shirt size={58} /><span>FASHION / TECHNOLOGY</span></div>
      </div>
      <div className="stats-grid">
        <div className="stat-card"><strong>{catalogueTotal || "—"}</strong><span>Catalogue items available</span></div>
        <div className="stat-card"><strong>{CATEGORIES.length}</strong><span>Clothing categories</span></div>
        <div className="stat-card"><strong>3</strong><span>Trained models</span></div>
        <div className="stat-card"><strong>{wardrobe.length}</strong><span>Wardrobe items</span></div>
      </div>
      <div className="section-heading"><p className="eyebrow">QUICK ACCESS</p><h2>Make something new</h2></div>
      <div className="feature-grid">
        {[["AI Fitting Room", Shirt, "Choose a garment and generate an image-based fitting result"], ["OOTD Stylist", Sparkles, "Build a rule-based outfit for your plans"], ["Explore Clothes", ShoppingBag, "Browse the fashion product catalogue"]].map(([name, Icon, text]) => (
          <button className="feature-card" key={name} onClick={() => selectPage(name)}><Icon size={22} /><h3>{name}</h3><p>{text}</p><span>Open section →</span></button>
        ))}
      </div>
      {featuredProducts.length > 0 && <><div className="section-heading"><p className="eyebrow">FROM THE CATALOGUE</p><h2>Featured pieces</h2></div><div className="mini-product-grid">{featuredProducts.map((product) => <button className="mini-product" key={product.id} onClick={() => { selectCatalogueGarment(product); selectPage("AI Fitting Room"); }}><ProductImage product={product} /><span>{product.category}</span><strong>{product.name}</strong></button>)}</div></>}
    </section>
  );

  const renderTryOn = () => (
    <section className="workspace">
      <p className="eyebrow">AI FASHION LAB</p><h1>Clothing recognition</h1>
      <p className="description">Upload a clothing image and compare predictions from VGG16, Custom CNN and ResNet50.</p>
      <div className="upload-area">
        <input type="file" accept="image/*" id="clothing-upload" onChange={handleImage} hidden />
        {image ? <img src={image} className="preview-image" alt="Selected clothing" /> : <label htmlFor="clothing-upload" className="upload-label"><Upload size={38} /><h3>Upload a clothing image</h3><p>JPG, PNG or another supported image</p></label>}
      </div>
      <div className="upload-actions"><label htmlFor="clothing-upload" className="secondary-button">Choose image</label><button className="hero-button" onClick={() => classifyImage()} disabled={!file || loading}>{loading ? <LoaderCircle className="spin" size={17} /> : <Sparkles size={17} />}{loading ? "Analysing..." : "Identify clothing"}</button><button className="secondary-button action-button" onClick={() => classifyImage(true)} disabled={!file || loading}>Compare all 3 models</button></div>
      {actionError && <p className="error-message">{actionError}</p>}
      {result && <div className="result-card"><p className="eyebrow">MODEL PREDICTION · VGG16</p><h2>{result.category}</h2><p>Confidence: <strong>{result.confidence}%</strong></p></div>}
      {comparison && <div className="result-card"><p className="eyebrow">MODEL COMPARISON</p><div className="comparison-grid">{Object.entries(comparison).map(([name, data]) => <div className="comparison-item" key={name}><h3>{name}</h3><p>{data.predicted_category}</p><strong>{data.confidence}%</strong><div className="confidence-track"><div className="confidence-fill" style={{ width: `${Math.min(data.confidence, 100)}%` }} /></div></div>)}</div></div>}
    </section>
  );

  const renderExplore = () => (
    <section className="catalogue"><p className="eyebrow">THE FASHION COLLECTION</p><h1>Find your next look.</h1><p className="description">Explore real fashion products from the clothing dataset.</p>
      <div className="category-filters"><button className={`filter-button ${selectedCategory === "All" ? "selected" : ""}`} onClick={() => setSelectedCategory("All")}>All</button>{CATEGORIES.map((category) => <button className={`filter-button ${selectedCategory === category ? "selected" : ""}`} key={category} onClick={() => setSelectedCategory(category)}>{category}</button>)}</div>
      <div className="catalogue-controls"><input value={catalogueSearch} onChange={(event) => setCatalogueSearch(event.target.value)} placeholder="Search catalogue" aria-label="Search catalogue" /><select value={catalogueSort} onChange={(event) => setCatalogueSort(event.target.value)} aria-label="Sort catalogue"><option value="default">Sort: curated order</option><option value="name">Name A–Z</option><option value="category">Category</option></select></div>
      {catalogueLoading ? <div className="empty-state"><LoaderCircle className="spin" /> Loading catalogue...</div> : catalogueError ? <div className="empty-state error-message">{catalogueError}</div> : (() => {
        const visibleProducts = products
          .filter((product) => product.name.toLowerCase().includes(catalogueSearch.toLowerCase()))
          .sort((left, right) => catalogueSort === "name" ? left.name.localeCompare(right.name) : catalogueSort === "category" ? left.category.localeCompare(right.category) : 0);
        return visibleProducts.length === 0 ? <div className="empty-state">No clothing products found.</div> : <div className="product-grid">{visibleProducts.map((product) => <div className="product-card" key={product.id}><ProductImage product={product} /><div className="product-info"><span>{product.category}</span><h3>{product.name}</h3><button className="select-product" onClick={() => { selectCatalogueGarment(product); selectPage("AI Fitting Room"); }}>Try this outfit</button></div></div>)}</div>;
      })()}
    </section>
  );

  const renderFittingRoom = () => (
    <section className="workspace fitting-workspace">
      <p className="eyebrow">IMAGE-BASED FITTING ROOM</p>
      <h1>Try on a complete look.</h1>
      <p className="description">Upload a clear, front-facing full-body photograph and choose a garment. The original image-processing pipeline generates the fitting result without overlays or mock images.</p>
      <div className="tryon-notice">The fitting pipeline performs garment masking, human parsing, pose extraction and image synthesis. CPU-only machines may be too slow or memory-limited for inference.</div>
      <div className="tryon-grid">
        <div className="tryon-panel"><p className="eyebrow">YOUR PHOTOGRAPH</p><div className="tryon-preview">{personImage ? <img src={personImage} alt="Your uploaded full-body photograph" /> : <label htmlFor="person-upload" className="tryon-upload"><Upload size={30} /><strong>Upload full-body photo</strong><span>JPG, JPEG, PNG or WEBP · max 10 MB</span></label>}</div><input id="person-upload" type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" onChange={handlePersonImage} hidden />{personImage && <label htmlFor="person-upload" className="secondary-button tryon-change">Change photo</label>}<p className="tryon-help">Use a clear, front-facing image with your full body visible.{personDimensions && ` Detected ${personDimensions.width}x${personDimensions.height}px.`}</p><p className="sample-label">Or try a sample model</p><div className="sample-image-list">{VTON_SAMPLE_PEOPLE.map((filename) => <button className="sample-image-button" key={filename} onClick={() => chooseSampleImage("image", filename)}><img src={`${API_BASE}/vton-examples/image/${filename}`} alt={`Sample model ${filename}`} /></button>)}</div></div>
        <div className="tryon-panel"><p className="eyebrow">SELECTED GARMENT</p><div className="tryon-preview">{selectedProduct ? <ProductImage product={selectedProduct} /> : garmentImage ? <img src={garmentImage} alt="Uploaded garment" /> : <label htmlFor="garment-upload" className="tryon-upload"><Shirt size={30} /><strong>Upload your garment</strong><span>Or choose one from Explore Clothes</span></label>}</div><input id="garment-upload" type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" onChange={handleGarmentImage} hidden /><div className="tryon-actions"><label htmlFor="garment-upload" className="secondary-button tryon-change">Upload garment</label><button className="secondary-button tryon-change" onClick={() => selectPage("Explore Clothes")}>Browse catalogue</button></div><p className="sample-label">Or try a sample garment</p><div className="sample-image-list">{VTON_SAMPLE_CLOTHES.map((filename) => <button className="sample-image-button" key={filename} onClick={() => chooseSampleImage("cloth", filename)}><img src={`${API_BASE}/vton-examples/cloth/${filename}`} alt={`Sample garment ${filename}`} /></button>)}</div><label className="garment-type">Garment type<select value={garmentCategory} onChange={(event) => setGarmentCategory(event.target.value)}><option value="upper_body">Upper body</option></select></label><p className="tryon-help">The cloned model currently supports upper-body garments. Use a clear top, shirt or jacket image.</p>{selectedProduct && <p className="tryon-help">{selectedProduct.name} · {selectedProduct.category}</p>}{garmentDimensions && <p className="tryon-help">Detected {garmentDimensions.width}x{garmentDimensions.height}px.</p>}</div>
        <div className="tryon-panel result-panel"><p className="eyebrow">GENERATED RESULT</p><div className="tryon-preview">{tryOnResult?.generated_image_data ? <img src={tryOnResult.generated_image_data} alt="AI-generated virtual try-on result" /> : <div className="result-placeholder"><Sparkles size={30} /><span>Your generated result will appear here.</span></div>}</div>{tryOnResult?.generated_image_data && <div className="tryon-actions"><a className="hero-button" href={tryOnResult.generated_image_data} download="vestiar-try-on.png">Download result</a><button className="secondary-button tryon-change" onClick={() => setShowTryOnComparison((visible) => !visible)}>{showTryOnComparison ? "Hide comparison" : "Compare images"}</button><button className="secondary-button tryon-change" onClick={saveTryOnResult}>Save to wardrobe</button><button className="secondary-button tryon-change" onClick={() => { setTryOnResult(null); setShowTryOnComparison(false); }}>Try another outfit</button></div>}{showTryOnComparison && tryOnResult?.generated_image_data && <div className="tryon-comparison"><div><p className="eyebrow">ORIGINAL</p><img src={personImage} alt="Original uploaded person" /></div><div><p className="eyebrow">RESULT</p><img src={tryOnResult.generated_image_data} alt="Generated virtual try-on result" /></div></div>}</div>
      </div>
      {tryOnError && <p className="error-message">{tryOnError}</p>}
      <div className="tryon-footer"><button className="hero-button" onClick={generateTryOn} disabled={!personFile || (!selectedProduct && !garmentFile) || tryOnLoading}>{tryOnLoading ? <LoaderCircle className="spin" size={17} /> : <Sparkles size={17} />}{tryOnLoading ? "Generating fitting result..." : "Generate Fitting Result"}</button>{tryOnLoading ? <span className="tryon-progress" role="status">{tryOnStage}...</span> : <span>Uses the original fitting checkpoints configured on the backend.</span>}</div>
      {savedTryOns.length > 0 && <div className="saved-tryons"><p className="eyebrow">SAVED TRY-ONS</p><div className="saved-tryon-list">{savedTryOns.map((item) => <img key={item.id} src={item.image} alt={`Saved try-on ${item.garment}`} />)}</div></div>}
    </section>
  );

  const renderStylist = () => (
    <section className="workspace"><p className="eyebrow">RULE-BASED OUTFIT BUILDER</p><h1>Outfit of the Day</h1><p className="description">Choose your preferences and receive at least 10 varied recommendations from the real catalogue.</p><div className="stylist-form">{[["Occasion", occasion, setOccasion, ["College", "Casual", "Party", "Traditional", "Formal", "Travel", "Special events"]], ["Weather", weather, setWeather, ["Hot", "Rainy", "Cold", "Any"]], ["Style", style, setStyle, ["Minimal", "Trendy", "Traditional", "Elegant", "Streetwear", "Casual chic"]], ["Clothing", clothingPreference, setClothingPreference, ["Western", "Ethnic", "Indo-Western", "Any"]]].map(([label, value, setter, options]) => <label key={label}>{label}<select value={value} onChange={(event) => setter(event.target.value)}>{options.map((option) => <option key={option}>{option}</option>)}</select></label>)}</div><button className="hero-button" onClick={generateOutfit}><Sparkles size={17} /> Generate recommendations</button>{outfit && <div className="outfit-result"><p className="eyebrow">YOUR RECOMMENDATION</p><div className="outfit-grid">{[["Recommended top", outfit.top], ["Bottom wear", outfit.bottom], ["Optional layer", outfit.layer]].map(([label, product]) => <div className="outfit-piece" key={label}><span>{label}</span>{product ? <><ProductImage product={product} /><strong>{product.name}</strong><small>{product.category}</small></> : <p>No catalogue layer needed</p>}</div>)}</div><p className="outfit-explanation">{outfit.explanation} Add neutral footwear and a simple accessory to complete the look.</p><div className="outfit-actions"><button className="secondary-button action-button" onClick={tryOutfit}>Try this outfit</button><button className="secondary-button action-button" onClick={saveOutfit}>Save outfit</button></div></div>}{outfitRecommendations.length > 0 && <div className="recommendation-section"><p className="eyebrow">MATCHED CATALOGUE PRODUCTS · {outfitRecommendations.length}</p><div className="mini-product-grid">{outfitRecommendations.map((product) => <button className="mini-product" key={product.id} onClick={() => { selectCatalogueGarment(product); selectPage("AI Fitting Room"); }}><ProductImage product={product} /><span>{product.category}</span><strong>{product.name}</strong></button>)}</div></div>}<div className="saved-outfits"><p className="eyebrow">SAVED OUTFITS</p>{savedOutfits.length ? savedOutfits.map((saved, index) => <div className="saved-outfit-row" key={saved.id}><span>Look {savedOutfits.length - index}</span><small>{saved.explanation}</small><button className="remove-button" onClick={() => toggleSavedOutfitFavourite(saved.id)}><Heart size={14} /> {saved.favourite ? "Favourited" : "Favourite"}</button></div>) : <p>No saved outfits yet.</p>}</div></section>
  );

  const renderWardrobe = () => (
    <section className="workspace"><p className="eyebrow">YOUR PERSONAL COLLECTION</p><h1>My Wardrobe</h1><p className="description">Images are stored in this browser. Uploading an item also runs the existing classifier to suggest its category.</p><form className="wardrobe-form" onSubmit={addWardrobeItem}><input value={wardrobeName} onChange={(event) => setWardrobeName(event.target.value)} placeholder="Item name" /><select value={wardrobeCategory} onChange={(event) => setWardrobeCategory(event.target.value)}>{CATEGORIES.map((category) => <option key={category}>{category}</option>)}</select><label className="secondary-button"><Upload size={15} /> Choose image<input type="file" accept="image/*" hidden onChange={handleWardrobeImage} /></label><button className="hero-button" type="submit"><Check size={16} /> Save item</button></form>{actionError && <p className="error-message">{actionError}</p>}<div className="catalogue-controls wardrobe-controls"><input value={wardrobeSearch} onChange={(event) => setWardrobeSearch(event.target.value)} placeholder="Search wardrobe" /><select value={wardrobeCategoryFilter} onChange={(event) => setWardrobeCategoryFilter(event.target.value)}><option>All</option>{CATEGORIES.map((category) => <option key={category}>{category}</option>)}</select></div>{wardrobe.length === 0 ? <div className="empty-state">Your wardrobe is empty. Add your first piece above.</div> : <div className="wardrobe-grid">{wardrobe.filter((item) => (wardrobeCategoryFilter === "All" || item.category === wardrobeCategoryFilter) && item.name.toLowerCase().includes(wardrobeSearch.toLowerCase())).map((item) => <div className="wardrobe-card" key={item.id}><img src={item.image} alt={item.name} /><div><span>{item.category}</span><h3>{item.name}</h3><div className="wardrobe-actions"><button className={`remove-button ${wardrobeFavorites.includes(item.id) ? "favourite" : ""}`} onClick={() => toggleWardrobeFavourite(item.id)}><Heart size={14} /> {wardrobeFavorites.includes(item.id) ? "Favourite" : "Favourite"}</button><button className="remove-button" onClick={() => setWardrobe((items) => items.filter((entry) => entry.id !== item.id))}><Trash2 size={14} /> Remove</button></div></div></div>)}</div>}</section>
  );

  const renderCompatibility = () => (
    <section className="workspace"><p className="eyebrow">STYLE CHECK</p><h1>Outfit Compatibility</h1><p className="description">Select saved wardrobe items to check garment roles, duplicates and basic colour cues from item names.</p>{wardrobe.length === 0 ? <div className="empty-state">Add wardrobe items first.</div> : <><div className="compatibility-grid">{wardrobe.map((item) => <button className={`compatibility-card ${compatibilityItems.some((entry) => entry.id === item.id) ? "selected" : ""}`} key={item.id} onClick={() => toggleCompatibilityItem(item)}><img src={item.image} alt={item.name} /><span>{item.category}</span><strong>{item.name}</strong></button>)}</div><button className="hero-button" onClick={analyseCompatibility} disabled={!compatibilityItems.length}>Analyse selected pieces</button>{compatibilityResult && <div className={`result-card ${compatibilityResult.tone === "Good foundation" ? "success-card" : ""}`}><p className="eyebrow">{compatibilityResult.tone}</p><h2>{compatibilityItems.length} pieces selected</h2><p>{compatibilityResult.explanation}</p></div>}</>}</section>
  );

  const renderSmartSearch = () => (
    <section className="workspace"><p className="eyebrow">VISUAL CATALOGUE SEARCH</p><h1>Find similar pieces</h1><p className="description">OpenCV compares HSV colour distributions against real catalogue images. This is visual similarity, not classification.</p><div className="upload-area"><input id="similar-search-upload" type="file" accept="image/*" onChange={searchSimilar} hidden />{searchPreview ? <img src={searchPreview} className="preview-image" alt="Similarity query" /> : <label htmlFor="similar-search-upload" className="upload-label"><Search size={38} /><h3>Upload a reference garment</h3><p>Search by visual appearance</p></label>}</div><label htmlFor="similar-search-upload" className="secondary-button">Choose reference image</label>{searchLoading && <div className="empty-state"><LoaderCircle className="spin" /> Comparing catalogue images...</div>}{searchError && <p className="error-message">{searchError}</p>}{similarProducts.length > 0 && <><p className="eyebrow search-method">HSV colour-distribution similarity</p><div className="product-grid">{similarProducts.map((product) => <div className="product-card" key={product.id}><ProductImage product={product} /><div className="product-info"><span>{product.category} · {product.similarity}% match</span><h3>{product.name}</h3><button className="select-product" onClick={() => { selectCatalogueGarment(product); selectPage("AI Fitting Room"); }}>Try this garment</button></div></div>)}</div></>}</section>
  );

  const renderPlanner = () => (
    <section className="workspace"><p className="eyebrow">WEEKLY EDIT</p><h1>Seven-day outfit planner</h1><p className="description">Assign saved outfits to Monday through Sunday. Your plan is stored locally in this browser.</p>{savedOutfits.length === 0 ? <div className="empty-state"><p>Save an outfit in OOTD Stylist before planning your week.</p><button className="hero-button planner-empty-action" onClick={() => selectPage("OOTD Stylist")}><Sparkles size={16} /> Create an outfit</button></div> : <div className="planner-grid">{plannerDays.map((day) => { const selected = savedOutfits.find((saved) => saved.id === weeklyPlan[day]); return <div className="planner-day" key={day}><strong>{day}</strong><select value={weeklyPlan[day] || ""} onChange={(event) => setWeeklyPlan((plan) => ({ ...plan, [day]: event.target.value || undefined }))}><option value="">No outfit planned</option>{savedOutfits.map((saved, index) => <option value={saved.id} key={saved.id}>Look {savedOutfits.length - index}</option>)}</select>{selected && <small>{selected.top?.name || "Saved outfit"}</small>}{weeklyPlan[day] && <button className="remove-button" onClick={() => setWeeklyPlan((plan) => { const next = { ...plan }; delete next[day]; return next; })}>Remove</button>}</div>; })}</div>}</section>
  );

  const renderIntelligence = () => {
    const distribution = CATEGORIES.map((category) => ({ category, count: history.filter((entry) => entry.category === category).length })).filter((entry) => entry.count);
    return <section className="page-content"><div className="page-header"><p className="eyebrow">FASHION INTELLIGENCE</p><h1>Your activity</h1><p className="description">Personal history from this browser, alongside the recorded model benchmark.</p></div><div className="stats-grid"><div className="stat-card"><strong>{history.length}</strong><span>Classifications recorded</span></div><div className="stat-card"><strong>{history.length ? `${Math.round(history.reduce((sum, item) => sum + item.confidence, 0) / history.length)}%` : "—"}</strong><span>Average prediction confidence</span></div><div className="stat-card"><strong>{wardrobeFavorites.length}</strong><span>Favourite wardrobe items</span></div><div className="stat-card"><strong>90.51%</strong><span>Best recorded test accuracy</span></div></div><div className="result-card"><p className="eyebrow">PREDICTION CATEGORY DISTRIBUTION</p>{distribution.length ? distribution.map((entry) => <div className="distribution-row" key={entry.category}><span>{entry.category}</span><div className="confidence-track"><div className="confidence-fill" style={{ width: `${Math.min(100, entry.count / history.length * 100)}%` }} /></div><strong>{entry.count}</strong></div>) : <div className="empty-state">Classify clothing images to build your personal history.</div>}</div><div className="result-card"><p className="eyebrow">RECENT PREDICTIONS</p>{history.slice(0, 8).map((entry) => <div className="history-row" key={entry.id}><span>{entry.category}</span><strong>{entry.confidence}%</strong><small>{new Date(entry.createdAt).toLocaleString()}</small></div>)}</div></section>;
  };

  const renderPerformance = () => (
    <section className="page-content"><div className="page-header"><p className="eyebrow">DEEP LEARNING ANALYSIS</p><h1>Model Performance</h1><p className="description">Recorded test results for the three preserved VestiAR classifiers.</p></div><div className="comparison-grid">{MODEL_RESULTS.map((model) => <div className={`comparison-item ${model.name === "ResNet50" ? "best-model" : ""}`} key={model.name}><span className="model-label">{model.name === "ResNet50" ? "HIGHEST ACCURACY" : "TEST RESULT"}</span><h3>{model.name}</h3><h2>{model.accuracy.toFixed(2)}%</h2><p>Test accuracy · loss {model.loss}</p><p>Parameters: {model.parameters.toLocaleString()}</p><div className="confidence-track"><div className="confidence-fill" style={{ width: `${model.accuracy}%` }} /></div><p className="architecture">{model.architecture}</p></div>)}</div><div className="result-card"><p className="eyebrow">EXPERIMENT SUMMARY</p><h2>ResNet50 leads at 90.51%</h2><p>These are the recorded test accuracy and loss values; no unrecorded validation metrics are shown.</p></div></section>
  );

  let content = page === "Dashboard" ? renderDashboard() : page === "AI Fitting Room" ? renderFittingRoom() : page === "Identify Clothing" ? renderTryOn() : page === "OOTD Stylist" ? renderStylist() : page === "Explore Clothes" ? renderExplore() : page === "Model Performance" ? renderPerformance() : page === "My Wardrobe" ? renderWardrobe() : page === "Compatibility Checker" ? renderCompatibility() : page === "Smart Fashion Search" ? renderSmartSearch() : page === "Weekly Planner" ? renderPlanner() : renderIntelligence();
  return <div className="app"><aside className="sidebar"><h2 className="logo">Vesti<span>AR.</span></h2><p className="side-label">YOUR SPACE</p>{MENU.map(({ name, icon: Icon }) => <button key={name} className={`nav-item ${page === name ? "active" : ""}`} onClick={() => selectPage(name)}><Icon size={19} />{name}</button>)}<div className="sidebar-bottom"><Sparkles size={20} /><p>Style is personal.<br />Make it yours.</p></div></aside><main className="main"><header className="topbar"><div><p className="greeting">YOUR PERSONAL FASHION SPACE</p><h2>{page}</h2></div><div className="profile">V</div></header>{content}</main></div>;
}

export default App;
