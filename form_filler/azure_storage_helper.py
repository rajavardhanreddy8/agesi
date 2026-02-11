"""
Azure Blob Storage Helper for PDF Management
Handles upload, public URL generation with SAS tokens, and deletion
"""

import os
import logging
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from azure.core.exceptions import ResourceNotFoundError

class AzureBlobClient:
    """Client for managing PDF uploads to Azure Blob Storage"""
    
    def __init__(self):
        """Initialize Azure Blob Storage client from environment variables"""
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.container_name = os.getenv('AZURE_STORAGE_CONTAINER', 'outing-submissions')
        
        if not self.connection_string:
            logging.warning("AZURE_STORAGE_CONNECTION_STRING not set - Azure Blob features disabled")
            self.blob_service_client = None
            return
        
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            self._ensure_container_exists()
        except Exception as e:
            logging.error(f"Failed to initialize Azure Blob client: {e}")
            self.blob_service_client = None
    
    def _ensure_container_exists(self):
        """Create container if it doesn't exist"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()
                logging.info(f"Created Azure storage container: {self.container_name}")
        except Exception as e:
            logging.warning(f"Container check/creation warning: {e}")
    
    def upload_pdf(self, pdf_buffer, filename):
        """
        Upload PDF buffer to Azure Blob Storage
        
        Args:
            pdf_buffer: BytesIO buffer containing PDF data
            filename: Name for the blob (e.g., 'outing_123_20260210.pdf')
        
        Returns:
            dict: {'blob_name': str, 'public_url': str}
        """
        if not self.blob_service_client:
            raise ValueError("Azure Blob Storage not initialized")
        
        try:
            blob_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Upload the PDF
            pdf_buffer.seek(0)  # Reset buffer position
            blob_client.upload_blob(pdf_buffer, overwrite=True, content_type='application/pdf')
            
            # Generate public URL with SAS token (valid for 2 hours)
            public_url = self.get_public_url(blob_name, expiry_hours=2)
            
            logging.info(f"Successfully uploaded PDF to Azure: {blob_name}")
            return {
                'blob_name': blob_name,
                'public_url': public_url
            }
        
        except Exception as e:
            logging.error(f"Failed to upload PDF to Azure: {e}")
            raise
    
    def get_public_url(self, blob_name, expiry_hours=2):
        """
        Generate public URL with SAS token for blob
        
        Args:
            blob_name: Name of the blob
            expiry_hours: Hours until SAS token expires (default 2)
        
        Returns:
            str: Public URL with SAS token
        """
        try:
            # Extract account name and key from connection string
            conn_parts = dict(item.split('=', 1) for item in self.connection_string.split(';') if '=' in item)
            account_name = conn_parts.get('AccountName')
            account_key = conn_parts.get('AccountKey')
            
            if not account_name or not account_key:
                raise ValueError("Could not extract account credentials from connection string")
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            # Construct full URL with SAS
            blob_url = f"https://{account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"
            
            return blob_url
        
        except Exception as e:
            logging.error(f"Failed to generate SAS URL: {e}")
            raise
    
    def delete_blob(self, blob_name):
        """
        Delete blob from Azure storage
        
        Args:
            blob_name: Name of the blob to delete
        
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.delete_blob()
            logging.info(f"Successfully deleted blob from Azure: {blob_name}")
            return True
        
        except ResourceNotFoundError:
            logging.warning(f"Blob not found for deletion: {blob_name}")
            return False
        
        except Exception as e:
            logging.error(f"Failed to delete blob from Azure: {e}")
            return False


# Convenience functions for use in api.py
_azure_client = None

def get_azure_client():
    """Get or create singleton Azure client"""
    global _azure_client
    if _azure_client is None:
        _azure_client = AzureBlobClient()
    return _azure_client

def upload_to_azure_blob(pdf_buffer, filename):
    """Upload PDF to Azure Blob Storage"""
    client = get_azure_client()
    return client.upload_pdf(pdf_buffer, filename)

def delete_from_azure_blob(blob_name):
    """Delete PDF from Azure Blob Storage"""
    client = get_azure_client()
    return client.delete_blob(blob_name)

def upload_signature_to_azure(image_base64, user_id):
    """
    Upload a signature image (base64) to Azure Blob Storage.
    Returns the permanent public URL.
    """
    import base64
    import uuid
    
    client = get_azure_client()
    
    if not client.blob_service_client:
        raise ValueError("Azure Blob Storage not initialized - check AZURE_STORAGE_CONNECTION_STRING")
    
    # Strip data URI prefix if present
    raw_b64 = image_base64
    content_type = 'image/png'
    if ',' in raw_b64:
        header, raw_b64 = raw_b64.split(',', 1)
        if 'jpeg' in header or 'jpg' in header:
            content_type = 'image/jpeg'
    
    image_bytes = base64.b64decode(raw_b64)
    
    # Ensure signatures container exists
    sig_container = 'signatures'
    try:
        container_client = client.blob_service_client.get_container_client(sig_container)
        if not container_client.exists():
            container_client.create_container(public_access='blob')
            logging.info(f"Created public Azure container: {sig_container}")
    except Exception as e:
        logging.warning(f"Signature container check: {e}")
    
    # Upload with unique name
    ext = 'jpg' if 'jpeg' in content_type else 'png'
    blob_name = f"sig_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
    blob_client = client.blob_service_client.get_blob_client(
        container=sig_container,
        blob=blob_name
    )
    blob_client.upload_blob(image_bytes, overwrite=True, content_type=content_type)
    
    # Build permanent public URL (no SAS needed for public container)
    conn_parts = dict(item.split('=', 1) for item in client.connection_string.split(';') if '=' in item)
    account_name = conn_parts.get('AccountName')
    public_url = f"https://{account_name}.blob.core.windows.net/{sig_container}/{blob_name}"
    
    logging.info(f"Uploaded signature to Azure: {public_url}")
    return public_url
