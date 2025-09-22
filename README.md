cd backend\
python main.py

cd frontend\
npm start

cd backend\
adk web

cd backend:\
-docker-compose down\
-docker-compose up -d\
-docker-compose logs -f\
-docker-compose build --no-cache

- TODO: Log all parts of the merging videos function to spot what is taking longer and improve eficiency.
- TODO: Create video processing to store information in the container. Video processing whenever it is uploaded with transctips, time stamps, metadata etc
- TODO: Add following agent specialized in analizing transcript context and organizing the merging order
- TODO: Move video processing to when user clicks edit button.
- TODO: Make sure merged videos have the same proportions for quality sake
