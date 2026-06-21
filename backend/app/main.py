app.add_middleware(
        CORSMiddleware,
        # We add the Vercel URL here explicitly to bypass the CORS block
        allow_origins=[
            "https://ai-study-buddy-h0rehpzdb-azeem-ahmad.vercel.app", 
            "http://localhost:3000" # Keep this for your local development
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )