<?php
$servername = "localhost";
$username = "root";
$password = ""; 
$dbname = "flask_db";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

$message = "";

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $personName = $_POST['person_name'];
    $occupation = $_POST['occupation'];

    // Handle the image upload
    if (isset($_FILES['image']) && $_FILES['image']['error'] === UPLOAD_ERR_OK) {
        $imageTmpPath = $_FILES['image']['tmp_name'];
        $imageName = basename($_FILES['image']['name']);
        $extension = pathinfo($imageName, PATHINFO_EXTENSION);
        $newImageName = $personName . "_face." . $extension;

        
        $uploadDir = 'C:/Users/FARHAN/Desktop/vscode@/dataset/';
        $relativePath = 'dataset/' . $newImageName;
        $dest_path = $uploadDir . $newImageName;

        if (move_uploaded_file($imageTmpPath, $dest_path)) {
            $imgPersonPath = $relativePath;

            
            $sql = "INSERT INTO img_dataset (prs_name, prs_occup, img_person) VALUES ('$personName', '$occupation', '$imgPersonPath')";
            
            if ($conn->query($sql) === TRUE) {
                $message = "New record created successfully";
            } else {
                $message = "Error: " . $sql . "<br>" . $conn->error;
            }
        } else {
            $message = "Error uploading the image.";
        }
    }
}

$conn->close();
?>


<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel</title>
    <style>
        .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 50px auto;
            width: 80%;
        }
        .form-container, .upload-container {
            width: 45%;
            margin-top: 2%;
        }
        .form-container {
            text-align: left;
            margin-left: 10rem;
        }
        .upload-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .form-container label {
            display: block;
            margin-bottom: 5px;
        }
        #person_name, #occupation {
            width: 100%;
        }
        input[type="text"], input[type="file"] {
            padding: 10px;
            margin: 10px 0;
            box-sizing: border-box;
        }
        button {
            padding: 10px 20px;
            background-color: #20c997;
            color: white;
            border: none;
            cursor: pointer;
            margin-top: 10px;
            width: 50%;
        }
        .heading1 {
            font-size: 2.5rem;
            color: #343a40;
            text-align: left;
            margin-top: 20px;
            margin-bottom: 20px;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }
        .message {
            text-align: center;
            margin-top: 20px;
            color: #20c997;
            font-weight: bold;
            font-size: 1.5rem;
        }
    </style>
</head>
<body>
<h1 class="heading1">OpenCV Face Recognition - Attendance Management System</h1>
<h3 style="font-size: 2.5rem; color: #20c997; text-align: center; margin-top: 80px; margin-bottom: 20px; font-weight: bold;">
        Admin Panel
</h3>

<div class="container">
    <div class="form-container">
        <form action="admin.php" method="post" enctype="multipart/form-data">
            <label for="person_name">Person Name:</label>
            <input type="text" name="person_name" id="person_name" required><br>
            
            <label for="occupation">Occupation:</label>
            <input type="text" name="occupation" id="occupation" required>
    </div>

    <div class="upload-container">
        <label for="image">Upload the Image Here:</label>
        <input type="file" name="image" id="image" required>
        <button type="submit">Submit</button>
        </form>

        
        <?php if (!empty($message)): ?>
            <div class="message"><?php echo $message; ?></div>
        <?php endif; ?>
    </div>
</div>

</body>
</html>

