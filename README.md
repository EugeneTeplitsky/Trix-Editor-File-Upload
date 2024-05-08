# Trix Editor File Upload

This project demonstrates how to integrate file upload functionality with the Trix editor using a Flask backend and a Vue.js frontend.

## Features

- Attach files to the Trix editor
- Upload attached files to the server
- Display upload progress
- Store uploaded files securely on the server
- Retrieve uploaded files from the server
- Authenticate API requests using a security token
- Migrate temporary files to permanent storage

## Prerequisites

- Python 3.x
- Node.js and npm
- Vue CLI

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/EugeneTeplitsky/trix-editor-file-upload.git
   cd trix-editor-file-upload
   ```

2. Set up the Flask server:

   - Create a virtual environment and activate it:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - Install the required dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Copy the `.env.sample` file to `.env` and update the configuration variables:
     ```bash
     cp .env.sample .env
     ```
   - Run the Flask server:
     ```bash
     flask run
     ```

## Configuration

The project uses environment variables for configuration. Make sure to update the `.env` files in both the `server` and `client` directories with your desired settings.

### Server Environment Variables

- `UPLOAD_FOLDER`: The directory where uploaded files will be stored.
- `MAX_FILE_SIZE`: The maximum size (in bytes) allowed for file uploads.
- `ALLOWED_EXTENSIONS`: The file extensions that are allowed for upload.
- `TEMP_FILE_EXPIRATION`: The number of days after which temporary files will be automatically deleted.
- `SECURITY_TOKEN`: The secret token used for authentication between the client and the server.
- `LOG_LEVEL`: The logging level for the application.
- `LOG_FILE`: The file path where the application logs will be written.

## API Endpoints

- `/upload` (POST): Uploads a file to the server and returns the generated filename.
- `/commit` (POST): Migrates a temporary file to permanent storage.
- `/files/<filename>` (GET): Retrieves an uploaded file from the server.

## Vue.js Usage Example

Here's a sample Vue.js component that demonstrates how to use the Trix editor with file upload functionality:

```vue
<template>
  <div>
    <trix-editor ref="trixEditor" @trix-attachment-add="handleAttachmentAdd"></trix-editor>
    <button @click="handleSubmit">Submit</button>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      securityToken: process.env.VUE_APP_SECURITY_TOKEN,
    };
  },
  methods: {
    handleAttachmentAdd(event) {
      if (event.attachment.file) {
        this.uploadFileAttachment(event.attachment);
      }
    },
    async uploadFileAttachment(attachment) {
      const file = attachment.file;
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await axios.post(`${process.env.VUE_APP_API_URL}/upload`, formData, {
          headers: {
            'X-Security-Token': this.securityToken,
          },
          onUploadProgress: (event) => {
            const progress = (event.loaded / event.total) * 100;
            attachment.setUploadProgress(progress);
          },
        });

        const filename = response.data.filename;
        const url = `${process.env.VUE_APP_API_URL}/files/${filename}`;
        attachment.setAttributes({ url, href: url });
      } catch (error) {
        console.error('Error uploading file:', error);
      }
    },
    async handleSubmit() {
      const content = this.$refs.trixEditor.editor.getDocument().toString();
      console.log('Editor content:', content);

      const attachments = this.$refs.trixEditor.editor.getAttachments();
      const filenames = attachments.map((attachment) => attachment.getAttribute('filename'));

      try {
        await axios.post(`${process.env.VUE_APP_API_URL}/commit`, { filenames }, {
          headers: {
            'X-Security-Token': this.securityToken,
          },
        });
        console.log('Files committed successfully');
      } catch (error) {
        console.error('Error committing files:', error);
      }
    },
  },
};
</script>
```

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
