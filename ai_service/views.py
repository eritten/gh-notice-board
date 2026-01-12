from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import openai
import os
from django.conf import settings


class ContentAnalysisView(APIView):
    """API endpoint for GPT-powered content analysis"""
    permission_classes = [AllowAny]

    def post(self, request):
        content = request.data.get('content', '')
        content_type = request.data.get('type', 'general')

        if not content:
            return Response({
                'error': 'Content is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            # Create context-aware prompt
            system_prompt = self._get_system_prompt(content_type)

            # Call GPT API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=0.7,
                max_tokens=800
            )

            analysis = response.choices[0].message.content

            return Response({
                'analysis': analysis,
                'content_type': content_type
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'AI analysis failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_system_prompt(self, content_type):
        prompts = {
            'news': """You are an expert content analyst for a Ghana-focused news platform.
            Analyze the provided news article and provide:
            1. Content quality assessment (clarity, accuracy, relevance)
            2. Suggested improvements for grammar, structure, and readability
            3. SEO recommendations (keywords, meta description)
            4. Fact-checking suggestions (areas that need verification)
            5. Engagement potential (how compelling is the content)
            Keep your response concise and actionable.""",

            'event': """You are an expert content analyst for event listings.
            Analyze the provided event description and provide:
            1. Completeness check (missing key details like date, venue, etc.)
            2. Clarity and appeal of the description
            3. Suggested improvements to attract more attendees
            4. Keywords and tags for better discoverability
            Keep your response concise and actionable.""",

            'opportunity': """You are an expert content analyst for job and scholarship postings.
            Analyze the provided opportunity description and provide:
            1. Clarity of requirements and qualifications
            2. Completeness (missing important details)
            3. Suggested improvements for better candidate attraction
            4. Keywords for better search visibility
            Keep your response concise and actionable.""",

            'general': """You are an expert content analyst.
            Analyze the provided content and provide:
            1. Overall quality assessment
            2. Grammar and style improvements
            3. Structure and readability suggestions
            4. SEO and engagement recommendations
            Keep your response concise and actionable."""
        }

        return prompts.get(content_type, prompts['general'])


class ContentSuggestionsView(APIView):
    """API endpoint for GPT-powered content suggestions"""
    permission_classes = [AllowAny]

    def post(self, request):
        topic = request.data.get('topic', '')
        content_type = request.data.get('type', 'news')
        context = request.data.get('context', '')

        if not topic:
            return Response({
                'error': 'Topic is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            # Create context-aware prompt
            system_prompt = self._get_suggestion_prompt(content_type)
            user_prompt = f"Generate content suggestions for: {topic}"
            if context:
                user_prompt += f"\n\nAdditional context: {context}"

            # Call GPT API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=600
            )

            suggestions = response.choices[0].message.content

            return Response({
                'suggestions': suggestions,
                'topic': topic,
                'content_type': content_type
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'AI suggestions failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_suggestion_prompt(self, content_type):
        prompts = {
            'news': """You are a creative content strategist for a Ghana-focused news platform.
            Generate engaging content suggestions including:
            1. 3-5 compelling article angles
            2. Potential headlines
            3. Key points to cover
            4. Relevant keywords for SEO
            Focus on topics relevant to Ghana and the Ghanaian diaspora.""",

            'event': """You are a creative event planner and content strategist.
            Generate engaging event content suggestions including:
            1. Event description ideas
            2. Activities and highlights
            3. Target audience identification
            4. Promotion strategies
            Focus on events relevant to Ghana and Ghanaian culture.""",

            'opportunity': """You are a career counselor and content strategist.
            Generate compelling opportunity content suggestions including:
            1. Description structure
            2. Key qualifications to highlight
            3. Benefits and selling points
            4. Application tips for candidates
            Focus on opportunities relevant to Ghana and Ghanaians.""",
        }

        return prompts.get(content_type, prompts['news'])


class ContentModerationView(APIView):
    """API endpoint for GPT-powered content moderation"""
    permission_classes = [AllowAny]

    def post(self, request):
        content = request.data.get('content', '')

        if not content:
            return Response({
                'error': 'Content is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            # Use GPT for content moderation
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a content moderator. Analyze the content for:
                        1. Inappropriate language or hate speech
                        2. Misinformation or false claims
                        3. Spam or promotional content
                        4. Sensitivity and cultural appropriateness for Ghana

                        Respond with a JSON-like structure:
                        - is_appropriate: true/false
                        - concerns: list of specific concerns (if any)
                        - recommendation: approve/review/reject
                        - explanation: brief explanation
                        """
                    },
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=400
            )

            moderation_result = response.choices[0].message.content

            return Response({
                'moderation': moderation_result,
                'content': content[:100] + '...' if len(content) > 100 else content
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'Content moderation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SmartSummarizationView(APIView):
    """API endpoint for GPT-powered content summarization"""
    permission_classes = [AllowAny]

    def post(self, request):
        content = request.data.get('content', '')
        length = request.data.get('length', 'medium')  # short, medium, long

        if not content:
            return Response({
                'error': 'Content is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            # Define length parameters
            length_config = {
                'short': {'words': 50, 'description': 'brief summary'},
                'medium': {'words': 150, 'description': 'concise summary'},
                'long': {'words': 300, 'description': 'detailed summary'}
            }

            config = length_config.get(length, length_config['medium'])

            # Call GPT API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an expert summarizer. Create a {config['description']}
                        of approximately {config['words']} words. Focus on key points and maintain
                        the core message. Make it engaging and easy to understand."""
                    },
                    {"role": "user", "content": content}
                ],
                temperature=0.5,
                max_tokens=500
            )

            summary = response.choices[0].message.content

            return Response({
                'summary': summary,
                'length': length,
                'original_length': len(content.split())
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'Summarization failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
